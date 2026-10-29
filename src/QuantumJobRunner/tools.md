# Tools: Quantum Job Runner

One tool per line, in the form `tool_name`: inputs → outputs. All tools are implemented in `src/phase1/quantum_lab.py` (circuit, run, and analysis tools), `src/web/server.py` / `src/phase1/main.py` (`ask_user`), and `src/phase1/agents.py` (`send_message`, `reply`).

## Planner tools

`list_algorithms`: no input → dict mapping each supported algorithm (`bell`, `ghz`, `grover`) to a short description of the circuit and its ideal output.

`build_circuit`: `algorithm` (str: `bell`, `ghz`, or `grover`), `num_qubits` (int; GHZ 2–5, Grover 2–4, Bell always 2), optional `target` (bitstring of length `num_qubits`, Grover only) → registers the circuit and returns `circuit_id`, `algorithm`, `num_qubits`, `depth`, `gate_counts`, `target`; or an error dict for invalid input.

`ask_user`: `question` (str) → shows the question to the User and returns `{"user_answer": <str>}`.

## Executor tools

`run_simulator`: `circuit_id` (str), `shots` (int, default 1024) → runs on the ideal noiseless Aer simulator, stores the result, and returns `job_id`, `backend` (`ideal_simulator`), `shots`, `top_counts` (top 8 outcomes).

`run_hardware`: `circuit_id` (str), `shots` (int, default 1024) → runs on the noisy `FakeBrisbane` simulated hardware, deducts the estimated cost (5 s + 0.01 s per shot) from the budget, stores the result, and returns `job_id`, `backend`, `shots`, `estimated_seconds`, `budget_remaining_seconds`, `simulator_run_first` (bool), `top_counts`.

`check_budget`: no input → `budget_total_seconds`, `budget_remaining_seconds`, `cost_model`.

## Analyst tools

`get_result`: `job_id` (str) → the stored result (`job_id`, `circuit_id`, `backend`, `shots`, counts limited to the top 8 outcomes, and `simulator_run_first` for hardware jobs); or an error if the job does not exist.

`compare_results`: `sim_job_id` (str), `hw_job_id` (str) → `total_variation_distance`, a note explaining TVD, the top 4 outcomes of each job (`sim_top`, `hw_top`), and, for Grover circuits, `target`, `sim_success_prob`, `hw_success_prob`.

## Shared actions (all agents)

`send_message`: `to` (agent name), `content` (str or JSON) → delivers the message through the orchestrator, waits for the recipient's turn to finish, and returns `{"reply_from": <agent>, "content": <reply>}`; or an error for an unknown agent or when the nesting depth limit is reached.

`reply`: `content` (str) → ends the agent's current turn and returns `content` to whoever sent the message (the User, for the Planner's top-level turn).
