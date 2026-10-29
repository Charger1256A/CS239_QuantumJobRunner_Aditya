# CS239 Quantum Job Runner (Aditya)

A multi-agent application that turns a plain-English request into a quantum circuit, runs it on an ideal simulator and on simulated IBM hardware (`FakeBrisbane`), and explains how hardware noise changed the result. Built for CS 239 Agentic Software Engineering.

| Agent | Role |
|---|---|
| **Planner** | Talks to the User, builds circuits, gets approval, coordinates the other agents |
| **Executor** | The only agent that runs circuits; holds the (dummy) IBM credentials |
| **Analyst** | Read-only; compares simulator and hardware results |

## Phase 1 deliverables

| Deliverable | Where |
|---|---|
| Requirements (what it does / must never do) | [`requirements.md`](requirements.md) → full: [`src/QuantumJobRunner/app.md`](src/QuantumJobRunner/app.md) |
| Policies (per agent: permission, capability, lifecycle, information flow, isolation) | [`policies.md`](policies.md) → full: [`src/QuantumJobRunner/policy.md`](src/QuantumJobRunner/policy.md) |
| Phase 1 source | [`src/phase1/`](src/phase1/) |
| Phase 1 traces (4, JSON + Markdown) | [`src/traces/phase1/`](src/traces/phase1/) |
| Traces README (each scenario and which policies it triggered) | [`src/traces/README.md`](src/traces/README.md) |
| Phase 2 source + traces | [`src/phase2/`](src/phase2/) *(not started)* |
| Tools, agent prompts, example episodes | [`src/QuantumJobRunner/`](src/QuantumJobRunner/) |
| Test cases | [`tests/README.md`](tests/README.md) |

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r src/requirements.txt
ollama pull qwen2.5:7b                 # or set LLM_BASE_URL / LLM_MODEL for a hosted model

python -m tests.smoke_test             # offline check, no LLM needed
cd src && python -m web.server         # demo website → http://localhost:8000
```

Full setup, environment variables, and run options are in [`src/README.md`](src/README.md).

## Repository layout

The layout follows the [CS239 submission guidelines](https://docs.google.com/document/d/1-hvS3KpJmbCQphmH4AAWofD073yIP6CCE4MTXoS8joQ/edit).

```
requirements.md, policies.md   Phase 1 summaries (link to the full files below)
src/
  README.md                    setup, dependencies, run instructions, env vars
  QuantumJobRunner/            application description (Archive 1)
    app.md                     purpose and supported tasks
    policy.md                  policies P1–P38
    tools.md                   tool names, inputs, outputs
    agents/                    one file per agent, with its actual system prompt
    episodes/                  example episodes (real Phase 1 runs)
  phase1/                      Phase 1 source
  phase2/                      Phase 2 (hardened) source
  traces/                      recorded traces + README
  web/                         demo website
tests/                         test cases (README.md) and the offline smoke test
```

## Building the submission archives

```bash
./package.sh <name> <uid>
```

This writes two files to `dist/`:
- `<name>-QuantumJobRunner-<uid>-requirements.tar.gz`: the `QuantumJobRunner/` folder
- `<name>-QuantumJobRunner-<uid>-whole.tar.gz`: `src/`, `tests/`, the READMEs, and `LICENSE`

## License

[MIT](LICENSE)
