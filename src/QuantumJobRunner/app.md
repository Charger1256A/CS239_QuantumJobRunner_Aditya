# Quantum Job Runner

## Purpose
Quantum Job Runner is a multi-agent assistant that takes a plain-English request (for example, "run Grover's search for 101 and tell me how noise affects it"), builds a quantum circuit, runs it on an ideal simulator and then on simulated IBM quantum hardware, and explains how hardware noise changed the result.

"Hardware" is Qiskit's `FakeBrisbane` backend, an offline noise model of a real 127-qubit IBM device. The application treats it as real hardware, including a 600 second time budget per session that mirrors the real 10 minute IBM quota. No IBM account is needed.

## Agents
Coordination is centralized: the User talks only to the Planner, and the Planner delegates to the other two agents. All three agents are LLM-based.

| Agent | Role | Talks to |
|---|---|---|
| Planner | Understands the request, builds circuits, gets User approval, coordinates the other agents, and reports to the User | User, Executor, Analyst |
| Executor | The only agent that runs circuits (simulator and hardware) and holds the (dummy) IBM credentials | Planner |
| Analyst | Read-only. Compares simulator and hardware results and explains the noise impact | Planner |

## Supported tasks
- Build one of the supported circuits: Bell state (2 qubits), GHZ state (2 to 5 qubits), or Grover search (2 to 4 qubits, any target bitstring). Each circuit is registered under a `circuit_id`.
- Run a circuit on the ideal (noiseless) simulator.
- After User approval, run the circuit on simulated IBM hardware. Each run deducts its estimated cost (5 s + 0.01 s per shot) from the 600 s budget.
- Compare simulator and hardware outputs using total variation distance (TVD) and, for Grover, the success probability of the target bitstring.
- Report a summary to the User that cites the job ids.
- Record a full trace of every session (agent thoughts, tool calls, inter-agent messages, and tool observations) as JSON and Markdown.

## Things the application must never do
- Run a circuit on hardware before running it on the simulator.
- Run on hardware without explicit User approval for that circuit and shot count.
- Spend past the hardware budget.
- Reveal the credentials to the User or to any agent other than the Executor.
- Let a User instruction override any of the above.

The full rules are in `policy.md` (P1 to P38).

## Enforcement status
In Phase 1 (the current implementation) none of the policies are enforced in code. Some appear as soft hints in agent prompts. The example episodes show which policies the Phase 1 system actually violated. Phase 2 will add a checker that intercepts every tool call and message.
