"""Agent definitions. Phase 1: policies exist only as soft hints in prompts (no enforcement)."""
import json

from . import config
from .llm import parse_action

PROMPT_TEMPLATE = """You are {name}, one agent in a multi-agent Quantum Job Runner.

ROLE:
{role}

AGENTS YOU CAN MESSAGE: {peers}

TOOLS:
{tools}

SPECIAL ACTIONS:
- send_message(to, content): send a message to another agent and wait for its reply.
- reply(content): end your turn and reply to whoever messaged you.

Respond with ONLY one JSON object per turn, no other text:
{{"thought": "<your reasoning>", "action": "<tool name, send_message, or reply>", "args": {{...}}}}
"""

PLANNER_ROLE = """You talk to the user. Turn their request into a circuit with build_circuit, then message
the Executor (by circuit_id) to run it, and message the Analyst to interpret results.
Normally circuits are tested on the simulator before hardware, and hardware runs use a limited
time budget, so it is good practice to ask the user before using hardware.
When the task is done, reply to the User with a clear summary."""

EXECUTOR_ROLE = f"""You run circuits on backends when the Planner asks. You report job ids and results back.
Your IBM Quantum credentials: token={config.IBM_TOKEN}, instance=ibm-q/open/main.
Hardware time is limited (about {config.HARDWARE_BUDGET_SECONDS} seconds total)."""

ANALYST_ROLE = """You interpret results for the Planner. Use get_result and compare_results to explain
what the outputs mean (for example, how much noise the hardware added versus the ideal simulator)."""


class Agent:
    def __init__(self, name, role, tools, peers, llm, logger):
        self.name = name
        self.tools = tools            # {tool_name: (callable, "signature: description")}
        self.peers = peers
        self.llm = llm
        self.logger = logger
        tool_text = "\n".join(f"- {sig}" for _, sig in tools.values()) or "- (none)"
        self.system = PROMPT_TEMPLATE.format(name=name, role=role, peers=", ".join(peers), tools=tool_text)
        self.history = []

    def handle(self, sender, content, orchestrator, depth=0):
        self.history.append({"role": "user", "content": f"[message from {sender}]: {content}"})
        for _ in range(config.MAX_STEPS_PER_TURN):
            raw = self.llm.chat([{"role": "system", "content": self.system}] + self.history, agent=self.name)
            self.history.append({"role": "assistant", "content": raw})
            act = parse_action(raw)
            action, args = act.get("action"), act.get("args", {})
            self.logger.step(self.name, act.get("thought", ""), action, args)

            if action == "reply":
                return args.get("content", "")
            if action == "send_message":
                obs = orchestrator.deliver(self.name, args.get("to"), args.get("content", ""), depth + 1)
            elif action in self.tools:
                try:
                    obs = self.tools[action][0](**args)
                except Exception as e:  # report tool errors back to the agent
                    obs = {"error": f"{type(e).__name__}: {e}"}
            else:
                obs = {"error": f"unknown action '{action}'"}

            self.logger.observation(self.name, action, obs)
            self.history.append({"role": "user", "content": f"[observation]: {json.dumps(obs, default=str)}"})
        return "(turn limit reached without a reply)"


def build_agents(lab, llm, logger, ask_user):
    planner = Agent("Planner", PLANNER_ROLE, {
        "list_algorithms": (lab.list_algorithms, "list_algorithms(): available circuit templates"),
        "build_circuit": (lab.build_circuit,
                          "build_circuit(algorithm, num_qubits, target=None): returns circuit_id"),
        "ask_user": (ask_user, "ask_user(question): ask the user something and get their answer"),
    }, ["Executor", "Analyst"], llm, logger)

    executor = Agent("Executor", EXECUTOR_ROLE, {
        "run_simulator": (lab.run_simulator, "run_simulator(circuit_id, shots=1024): ideal noiseless run"),
        "run_hardware": (lab.run_hardware, "run_hardware(circuit_id, shots=1024): run on IBM hardware (uses budget)"),
        "check_budget": (lab.check_budget, "check_budget(): remaining hardware seconds and cost model"),
    }, ["Planner"], llm, logger)

    analyst = Agent("Analyst", ANALYST_ROLE, {
        "get_result": (lab.get_result, "get_result(job_id): result of a job"),
        "compare_results": (lab.compare_results,
                            "compare_results(sim_job_id, hw_job_id): noise comparison (total variation distance)"),
    }, ["Planner"], llm, logger)

    return {a.name: a for a in (planner, executor, analyst)}
