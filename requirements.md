# Requirements: Quantum Job Runner

## Overview
A multi-agent assistant that takes a natural-language request (for example, "run Grover's search for 101 and tell me how noise affects it"), builds a quantum circuit, runs it on an ideal simulator and on (simulated) IBM quantum hardware, and explains how hardware noise changed the result.

**Hardware note:** real IBM hardware time is limited to 10 minutes, so "hardware" runs use Qiskit's `FakeBrisbane` backend: an offline replica of a real 127-qubit IBM device with its actual noise characteristics. The app treats it as real hardware, including a 600 second budget.

## Agents
| Agent | Role | Talks to |
|---|---|---|
| **Planner** | Understands the user's request, builds circuits, gets user approval, coordinates the others, reports to the user | User, Executor, Analyst |
| **Executor** | The only agent that runs circuits (simulator and hardware) and holds IBM credentials | Planner |
| **Analyst** | Read-only. Compares simulator and hardware results and explains the noise impact | Planner |

## Functional requirements (what it does)
- **FR-1:** Accept a natural-language request for one of the supported algorithms: Bell state, GHZ state (2 to 5 qubits), or Grover search (2 to 4 qubits, any target bitstring).
- **FR-2:** Build the circuit and register it under a `circuit_id`.
- **FR-3:** Run the circuit on an ideal (noiseless) simulator.
- **FR-4:** After user approval, run the circuit on simulated IBM hardware, deducting estimated time from a 600 second budget.
- **FR-5:** Compare simulator and hardware outputs using total variation distance (TVD) and, for Grover, success probability of the target.
- **FR-6:** Report a clear summary to the user with job ids.
- **FR-7:** Record a complete trace (thoughts, actions, inter-agent messages, observations) of every session as JSON and Markdown.

## Must never do
- **MN-1:** Run a circuit on hardware without first running it on the simulator.
- **MN-2:** Run on hardware without explicit user approval for that circuit and shot count.
- **MN-3:** Spend beyond the hardware budget (the budget must never go negative).
- **MN-4:** Reveal credentials (API token, instance) to the user or to any agent other than the Executor.
- **MN-5:** Let the Analyst or Planner trigger a run directly, bypassing the Executor.
- **MN-6:** Report results that did not come from a tool observation, or present simulated hardware results as real hardware.
- **MN-7:** Let a user instruction override any of the above.

Full per-agent rules are in [`policies.md`](policies.md).

## Non-functional requirements
- Works with any OpenAI-compatible LLM endpoint (local via Ollama, or hosted), configured by environment variables.
- Runs fully offline apart from the LLM; no IBM account needed.
- Each session is isolated (fresh circuits, results, and budget).
