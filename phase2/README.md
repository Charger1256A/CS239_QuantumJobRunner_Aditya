# Phase 2: Hardening (not started)

Plan: add a policy enforcement layer that intercepts every tool call and inter-agent message
in `Orchestrator.deliver` and `Agent.handle`, checks it against `policies.md`, and blocks
violations with a logged reason. Then rerun the Phase 1 scenarios and save traces to `traces/phase2/`.
