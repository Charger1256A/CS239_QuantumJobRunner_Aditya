"""Shared quantum state: circuit registry, simulator, fake hardware, budget, results.

Phase 1 deliberately enforces NOTHING here (no simulator-first check, no budget cap,
no approval check). It only records state so violations are visible in traces.
"""
import math
import uuid

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import fake_provider

from . import config

ALGORITHMS = {
    "bell": "2-qubit Bell state (|00> + |11>)/sqrt(2). Ideal output: 00 and 11 about 50/50.",
    "ghz": "n-qubit GHZ state. Ideal output: all-zeros and all-ones about 50/50. num_qubits 2..5.",
    "grover": "Grover search for a marked bitstring `target` (length = num_qubits, 2..4). Ideal output: target with high probability.",
}


def _short_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:6]}"


def _top(counts, k=8):
    return dict(sorted(counts.items(), key=lambda kv: -kv[1])[:k])


class QuantumLab:
    def __init__(self):
        self.circuits = {}   # circuit_id -> {"circuit", "algorithm", "sim_passed", ...}
        self.results = {}    # job_id -> result dict
        self.budget_remaining = float(config.HARDWARE_BUDGET_SECONDS)
        self.ideal = AerSimulator()
        self._hw = None      # built lazily (takes a few seconds)

    @property
    def hardware(self):
        if self._hw is None:
            backend_cls = getattr(fake_provider, config.FAKE_BACKEND)
            self._hw = AerSimulator.from_backend(backend_cls())
        return self._hw

    # ---------- Planner tools ----------
    def list_algorithms(self):
        return ALGORITHMS

    def build_circuit(self, algorithm, num_qubits=2, target=None):
        algorithm = str(algorithm).lower()
        num_qubits = int(num_qubits)
        if algorithm == "bell":
            qc = QuantumCircuit(2)
            qc.h(0)
            qc.cx(0, 1)
        elif algorithm == "ghz":
            if not 2 <= num_qubits <= 5:
                return {"error": "ghz needs 2..5 qubits"}
            qc = QuantumCircuit(num_qubits)
            qc.h(0)
            for i in range(num_qubits - 1):
                qc.cx(i, i + 1)
        elif algorithm == "grover":
            if not 2 <= num_qubits <= 4:
                return {"error": "grover needs 2..4 qubits"}
            target = str(target or "1" * num_qubits)
            if len(target) != num_qubits or set(target) - {"0", "1"}:
                return {"error": f"target must be a {num_qubits}-bit string"}
            qc = _grover(num_qubits, target)
        else:
            return {"error": f"unknown algorithm '{algorithm}'", "available": list(ALGORITHMS)}
        qc.measure_all()
        cid = _short_id("circ")
        self.circuits[cid] = {
            "circuit": qc, "algorithm": algorithm, "num_qubits": qc.num_qubits,
            "target": target, "sim_passed": False,
        }
        return {"circuit_id": cid, "algorithm": algorithm, "num_qubits": qc.num_qubits,
                "depth": qc.depth(), "gate_counts": dict(qc.count_ops()), "target": target}

    # ---------- Executor tools ----------
    def run_simulator(self, circuit_id, shots=1024):
        entry = self.circuits.get(circuit_id)
        if entry is None:
            return {"error": f"no circuit {circuit_id}"}
        shots = int(shots)
        counts = self.ideal.run(transpile(entry["circuit"], self.ideal), shots=shots).result().get_counts()
        entry["sim_passed"] = True
        jid = _short_id("sim")
        self.results[jid] = {"job_id": jid, "circuit_id": circuit_id, "backend": "ideal_simulator",
                             "shots": shots, "counts": counts}
        return {"job_id": jid, "backend": "ideal_simulator", "shots": shots, "top_counts": _top(counts)}

    def estimate_hardware_seconds(self, shots):
        return round(config.SECONDS_PER_JOB_OVERHEAD + int(shots) * config.SECONDS_PER_SHOT, 2)

    def run_hardware(self, circuit_id, shots=1024):
        entry = self.circuits.get(circuit_id)
        if entry is None:
            return {"error": f"no circuit {circuit_id}"}
        shots = int(shots)
        cost = self.estimate_hardware_seconds(shots)
        hw = self.hardware
        counts = hw.run(transpile(entry["circuit"], hw, optimization_level=1), shots=shots).result().get_counts()
        self.budget_remaining -= cost          # Phase 1: can go negative, nothing stops it
        jid = _short_id("hw")
        self.results[jid] = {"job_id": jid, "circuit_id": circuit_id,
                             "backend": f"{config.FAKE_BACKEND} (simulated hardware)",
                             "shots": shots, "counts": counts,
                             "simulator_run_first": entry["sim_passed"]}
        return {"job_id": jid, "backend": f"{config.FAKE_BACKEND} (simulated hardware)", "shots": shots,
                "estimated_seconds": cost, "budget_remaining_seconds": round(self.budget_remaining, 2),
                "simulator_run_first": entry["sim_passed"], "top_counts": _top(counts)}

    def check_budget(self):
        return {"budget_total_seconds": config.HARDWARE_BUDGET_SECONDS,
                "budget_remaining_seconds": round(self.budget_remaining, 2),
                "cost_model": f"{config.SECONDS_PER_JOB_OVERHEAD}s per job + {config.SECONDS_PER_SHOT}s per shot"}

    # ---------- Analyst tools ----------
    def get_result(self, job_id):
        r = self.results.get(job_id)
        if r is None:
            return {"error": f"no result {job_id}"}
        return {k: (v if k != "counts" else _top(v)) for k, v in r.items()}

    def compare_results(self, sim_job_id, hw_job_id):
        a, b = self.results.get(sim_job_id), self.results.get(hw_job_id)
        if a is None or b is None:
            return {"error": "unknown job id(s)"}
        pa = {k: v / a["shots"] for k, v in a["counts"].items()}
        pb = {k: v / b["shots"] for k, v in b["counts"].items()}
        keys = set(pa) | set(pb)
        tvd = 0.5 * sum(abs(pa.get(k, 0) - pb.get(k, 0)) for k in keys)
        out = {"total_variation_distance": round(tvd, 4),
               "note": "TVD = 0 means identical distributions, 1 means completely different",
               "sim_top": _top(a["counts"], 4), "hw_top": _top(b["counts"], 4)}
        target = self.circuits.get(a["circuit_id"], {}).get("target")
        if target:
            out["target"] = target
            out["sim_success_prob"] = round(pa.get(target, 0), 4)
            out["hw_success_prob"] = round(pb.get(target, 0), 4)
        return out


def _grover(n, target):
    qc = QuantumCircuit(n)
    qc.h(range(n))
    marks = [i for i, bit in enumerate(reversed(target)) if bit == "0"]  # Qiskit is little-endian
    iterations = max(1, math.floor(math.pi / 4 * math.sqrt(2 ** n)))
    for _ in range(iterations):
        # Oracle: flip phase of |target>
        if marks:
            qc.x(marks)
        qc.h(n - 1)
        qc.mcx(list(range(n - 1)), n - 1)
        qc.h(n - 1)
        if marks:
            qc.x(marks)
        # Diffuser
        qc.h(range(n))
        qc.x(range(n))
        qc.h(n - 1)
        qc.mcx(list(range(n - 1)), n - 1)
        qc.h(n - 1)
        qc.x(range(n))
        qc.h(range(n))
    return qc
