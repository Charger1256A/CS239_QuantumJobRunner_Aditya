"""Offline smoke test using a scripted (fake) LLM so you can check the pipeline without a model.
These traces are NOT submission traces. Run: python -m tests.smoke_test"""
import json
import tempfile

from phase1.llm import ScriptedLLM
from phase1.main import SCENARIO_DIR, run_scenario

S = lambda thought, action, **args: {"thought": thought, "action": action, "args": args}


def main():
    script = {
        "Planner": [
            S("Build the circuit.", "build_circuit", algorithm="grover", num_qubits=3, target="101"),
            S("Ask Executor to simulate.", "send_message", to="Executor", content="Simulate the circuit"),
            S("Approval needed.", "ask_user", question="OK to use hardware?"),
            S("Run on hardware.", "send_message", to="Executor", content="Run on hardware"),
            S("Done.", "reply", content="Finished."),
        ],
        "Executor": [
            S("Run sim.", "run_simulator", circuit_id="CID", shots=512),
            S("Report.", "reply", content="sim ok"),
            S("Run hw.", "run_hardware", circuit_id="CID", shots=512),
            S("Report.", "reply", content="hw ok"),
        ],
    }
    llm = ScriptedLLM(script)
    # Patch circuit id once known
    from phase1 import quantum_lab
    orig = quantum_lab.QuantumLab.build_circuit

    def build(self, *a, **k):
        r = orig(self, *a, **k)
        for q in llm.queues["Executor"]:
            q["args"]["circuit_id"] = r["circuit_id"]
        return r

    quantum_lab.QuantumLab.build_circuit = build
    scenario = json.load(open(SCENARIO_DIR / "01_happy_path.json"))
    with tempfile.TemporaryDirectory() as d:
        final, (jp, mp) = run_scenario(scenario, llm, d)
        events = json.load(open(jp))["events"]
        print("final:", final, "| events:", len(events))
        print(open(mp).read()[:1500])
    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    main()
