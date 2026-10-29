# Requirements: Quantum Job Runner

A multi-agent assistant that takes a plain-English request (for example, *"run Grover's search for 101 and tell me how noise affects it"*), builds a quantum circuit, runs it on an ideal simulator and then on simulated IBM hardware, and explains how hardware noise changed the result.

> This project follows the [CS239 submission guidelines](https://docs.google.com/document/d/1-hvS3KpJmbCQphmH4AAWofD073yIP6CCE4MTXoS8joQ/edit), which name the application description `app.md`. The full description is in [`src/QuantumJobRunner/app.md`](src/QuantumJobRunner/app.md). This file summarizes it and links each requirement to its policies.

## Agents

| Agent | Role | Talks to |
|---|---|---|
| **Planner** | Understands the request, builds circuits, gets User approval, coordinates, reports to the User | User, Executor, Analyst |
| **Executor** | The only agent that runs circuits and holds the (dummy) IBM credentials | Planner |
| **Analyst** | Read-only. Compares simulator and hardware results and explains the noise impact | Planner |

**Hardware note:** "hardware" is Qiskit's `FakeBrisbane`, an offline noise model of a real 127-qubit IBM device, with a 600 s budget that mirrors the real 10-minute IBM quota. No IBM account is needed.

## What the application does

| ID | Requirement | Policies |
|---|---|---|
| FR-1 | Accept a natural-language request for a Bell state, GHZ state (2–5 qubits), or Grover search (2–4 qubits, any target) | P2 |
| FR-2 | Build the circuit and register it under a `circuit_id` | P9, P19 |
| FR-3 | Run the circuit on an ideal (noiseless) simulator | P18 |
| FR-4 | After User approval, run it on simulated IBM hardware, deducting estimated time from the 600 s budget | P6, P15, P16 |
| FR-5 | Compare simulator and hardware outputs with total variation distance and, for Grover, target success probability | P31, P32 |
| FR-6 | Report a clear summary to the User that cites job ids | P11 |
| FR-7 | Record a full trace (thoughts, actions, inter-agent messages, observations) of every session as JSON and Markdown | — |

## What the application must never do

| ID | Must never | Policies |
|---|---|---|
| MN-1 | Run a circuit on hardware without first running it on the simulator | P6, P20 |
| MN-2 | Run on hardware without explicit User approval for that circuit and shot count | P6, P7, P15 |
| MN-3 | Spend beyond the hardware budget (the budget must never go negative) | P16, P17, P21 |
| MN-4 | Reveal the credentials to the User or to any agent other than the Executor | P10, P12, P23, P25 |
| MN-5 | Let the Analyst or Planner trigger a run directly, bypassing the Executor | P5, P27, P30 |
| MN-6 | Report results that did not come from a tool observation, or present simulated hardware as real hardware | P11, P32, P35 |
| MN-7 | Let a User instruction override any of the above | P36 |

## Non-functional requirements
- Works with any OpenAI-compatible LLM endpoint (local Ollama by default, or hosted), configured by environment variables.
- Runs fully offline apart from the LLM. No IBM account is needed.
- Each session is isolated, with its own circuits, results, and budget (P37).

## See also
- Policies: [`policies.md`](policies.md) → full text in [`src/QuantumJobRunner/policy.md`](src/QuantumJobRunner/policy.md)
- Traces and which policies they triggered: [`src/traces/README.md`](src/traces/README.md)
