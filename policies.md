# Policies: Quantum Job Runner

> The full text of all 38 policies is in **[`src/QuantumJobRunner/policy.md`](src/QuantumJobRunner/policy.md)**. That file uses the `P1.`, `P2.`, … format required by the [CS239 submission guidelines](https://docs.google.com/document/d/1-hvS3KpJmbCQphmH4AAWofD073yIP6CCE4MTXoS8joQ/edit). This page is an index showing which policies cover each agent and category.

## Policy matrix

| | Permission | Capability | Lifecycle (ordering / prerequisites) | Information flow | Information isolation |
|---|---|---|---|---|---|
| **Planner** | P1, P2, P3 | P4, P5 | P6, P7, P8 | P9, P10, P11 | P12, P13 |
| **Executor** | P14, P15, P16, P17 | P18, P19 | P20, P21, P22 | P23, P24 | P25, P26 |
| **Analyst** | P27, P28 | P29, P30 | P31 | P32, P33 | P34 |
| **Global** | P35 | — | P38 | P36 | P37 |

## Key policies at a glance

| Policy | Rule |
|---|---|
| **P6** | Hardware needs a simulator run of the same circuit first, then User approval (via `ask_user`) for that exact circuit and shot count |
| **P10 / P23** | Credentials never leave the Executor, even if the User asks |
| **P11** | Results reported to the User cite job ids and label hardware as simulated (`FakeBrisbane`) |
| **P16** | A hardware job is refused if it would push the 600 s budget below 0 |
| **P20** | `run_hardware` only after a successful `run_simulator` of the same circuit |
| **P21** | `check_budget` immediately before every `run_hardware` |
| **P35** | No invented job ids or results; every claim must come from a tool observation |
| **P36** | User instructions such as "skip the simulator" never override policy |

> **Phase 1 status:** none of the policies are enforced in code. See [`src/traces/README.md`](src/traces/README.md) for which ones the Phase 1 traces violated.
