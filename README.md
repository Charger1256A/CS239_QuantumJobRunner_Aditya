# CS239 Quantum Job Runner (Aditya)

A multi-agent app that turns a plain-English request into a quantum circuit, runs it on an ideal simulator and on simulated IBM hardware, and explains how hardware noise changed the result. Built for CS 239 Agentic Software Engineering.

- **Planner:** talks to the user, builds circuits, gets approval, coordinates
- **Executor:** the only agent that runs circuits and holds (dummy) IBM credentials
- **Analyst:** read-only, compares simulator vs hardware results

"Hardware" is Qiskit's `FakeBrisbane`, an offline noise model of a real 127-qubit IBM device, so no IBM account or quota is used.

See [`requirements.md`](requirements.md), [`policies.md`](policies.md), and [`traces/README.md`](traces/README.md).

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**Model used for the Phase 1 traces:** `qwen2.5:7b`, run locally with Ollama (used instead of the class-recommended Zeno, which took long to install).
**LLM:** any OpenAI-compatible endpoint. Default is local Ollama:
```bash
ollama pull qwen2.5:7b      # any instruction-following model that outputs JSON well
export LLM_MODEL=qwen2.5:7b # see .env.example for hosted options
```

## Run
```bash
python -m tests.smoke_test                                         # offline check, no LLM needed
python -m phase1.main --scenario phase1/scenarios/01_happy_path.json
python -m phase1.main --all                                         # all scenarios -> traces/phase1/
```

## Layout
```
phase1/
  agents.py         agent loop + the 3 agent definitions and prompts
  orchestrator.py   routes messages between agents (no policy checks in Phase 1)
  quantum_lab.py    circuits, ideal simulator, fake hardware, budget, result comparison
  trace_logger.py   saves JSON + Markdown traces
  scenarios/        one JSON file per trace scenario
phase2/             hardened version (Phase 2)
traces/             generated traces + README
```

## License
MIT
