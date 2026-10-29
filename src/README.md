# CS239 Quantum Job Runner (Aditya)

A multi-agent app that turns a plain-English request into a quantum circuit, runs it on an ideal simulator and on simulated IBM hardware, and explains how hardware noise changed the result. Built for CS 239 Agentic Software Engineering.

- **Planner:** talks to the user, builds circuits, gets approval, coordinates
- **Executor:** the only agent that runs circuits and holds (dummy) IBM credentials
- **Analyst:** read-only, compares simulator vs hardware results

The application description, policies, tools, agent prompts, and example episodes are in [`QuantumJobRunner/`](QuantumJobRunner/). Test cases are described in [`../tests/README.md`](../tests/README.md).

## Dependencies
- Python 3.10+
- Python packages in `requirements.txt` (Qiskit, Qiskit Aer, `qiskit-ibm-runtime` for the `FakeBrisbane` noise model, and `openai` as the LLM client)
- An OpenAI-compatible LLM endpoint (local Ollama by default)

## External services
- **LLM (required for real runs):** any OpenAI-compatible chat completions endpoint. The default is a local [Ollama](https://ollama.com) server, so no API key is needed.
- **IBM Quantum: not required.** "Hardware" is Qiskit's `FakeBrisbane`, an offline noise model of a real 127-qubit IBM device, so no IBM account or quota is used. The token in `phase1/config.py` is a dummy (`FAKE_TOKEN_123`).

## Setup
From the repository root:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r src/requirements.txt
```

Start the LLM (default: local Ollama):
```bash
ollama pull qwen2.5:7b      # any instruction-following model that outputs JSON well
```

## Environment variables
All are optional. Defaults are shown. See `.env.example` for a hosted-endpoint example.

| Variable | Default | Meaning |
|---|---|---|
| `LLM_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible endpoint (Ollama default) |
| `LLM_API_KEY` | `ollama` | API key for the endpoint |
| `LLM_MODEL` | `qwen2.5:7b` | Model name |
| `LLM_TEMPERATURE` | `0.2` | Sampling temperature |

**Model used for the Phase 1 traces:** `qwen2.5:7b`, run locally with Ollama (used instead of the class-recommended Zeno, which took long to install).

## Run
Run from inside `src/`:
```bash
cd src
python -m phase1.main --scenario phase1/scenarios/01_happy_path.json   # one scenario
python -m phase1.main --all                                            # all scenarios -> traces/phase1/
```

### Demo website
Type your own request and watch the agents talk to each other live:
```bash
cd src
python -m web.server            # then open http://localhost:8000  (--port to change)
```
- **Live tab:** your request goes to the real agents. Each message, thought, tool call and result appears in a sequence diagram as it happens. When the Planner calls `ask_user`, an answer box appears and the run waits for you (Approve / Deny / type a reply).
- **Replay tab:** plays back a recorded trace from `traces/`. No LLM is needed, so it works as a backup if the model is slow or offline.
- **Policy monitor:** flags P10, P11, P15, P16, P17, P20, P21 and P23 violations as they happen (display only, not enforced).
- Live runs are saved to `traces/web/` (git-ignored).

Offline check, no LLM needed (run from the repository root):
```bash
python -m tests.smoke_test
```

## Example usage
```bash
cd src
python -m phase1.main --scenario phase1/scenarios/01_happy_path.json
```
This sends the request *"Run Grover's search on 3 qubits to find the bitstring 101. Test it on the simulator, then on IBM hardware, and tell me how much the hardware noise hurt the success rate."* to the Planner. The script prints the Planner's final answer and writes `traces/phase1/01_happy_path.json` and `.md`. A sample run gave about 97% success on the simulator and about 66% on FakeBrisbane.

To try your own request, copy a scenario file and edit `user_request` (and `user_replies`, the scripted answers given to `ask_user`).

## Layout
```
src/
  phase1/
    agents.py         agent loop + the 3 agent definitions and prompts
    orchestrator.py   routes messages between agents (no policy checks in Phase 1)
    quantum_lab.py    circuits, ideal simulator, fake hardware, budget, result comparison (the tools)
    llm.py            OpenAI-compatible client, scripted test LLM, action parser
    trace_logger.py   saves JSON + Markdown traces
    config.py         LLM settings, budget, cost model, loop limits
    scenarios/        one JSON file per trace scenario
  web/                demo website (server.py + static/index.html), standard library only
  phase2/             hardened version (Phase 2, not started)
  traces/             generated traces + README
```

## License
MIT (see `../LICENSE`)
