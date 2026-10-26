"""Run one scenario and save its trace.

  python -m phase1.main --scenario phase1/scenarios/01_happy_path.json
  python -m phase1.main --all
"""
import argparse
import glob
import json

from .agents import build_agents
from .llm import OpenAICompatibleLLM
from .orchestrator import Orchestrator
from .quantum_lab import QuantumLab
from .trace_logger import TraceLogger


def run_scenario(scenario, llm, out_dir="traces/phase1"):
    logger = TraceLogger(scenario, getattr(llm, "model", "unknown"))
    replies = list(scenario.get("user_replies", []))

    def ask_user(question):
        logger.message("Planner", "User", question)
        answer = replies.pop(0) if replies else "(no answer: user is unavailable)"
        logger.message("User", "Planner", answer)
        return {"user_answer": answer}

    lab = QuantumLab()
    agents = build_agents(lab, llm, logger, ask_user)
    final = Orchestrator(agents, logger).run(scenario["user_request"])
    paths = logger.save(out_dir)
    return final, paths


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scenario", help="path to a scenario JSON file")
    p.add_argument("--all", action="store_true", help="run every scenario in phase1/scenarios")
    p.add_argument("--out", default="traces/phase1")
    a = p.parse_args()

    files = sorted(glob.glob("phase1/scenarios/*.json")) if a.all else [a.scenario]
    if not files or files == [None]:
        p.error("give --scenario PATH or --all")
    llm = OpenAICompatibleLLM()
    for f in files:
        with open(f) as fh:
            scenario = json.load(fh)
        print(f"\n=== {scenario['id']}: {scenario['title']} ===")
        final, paths = run_scenario(scenario, llm, a.out)
        print("Final answer to user:\n", final)
        print("Trace saved:", *paths)


if __name__ == "__main__":
    main()
