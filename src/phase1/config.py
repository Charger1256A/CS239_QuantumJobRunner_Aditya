"""Central configuration. Override LLM settings with environment variables."""
import os

# LLM (any OpenAI-compatible endpoint: Ollama, LM Studio, vLLM, OpenAI, etc.)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")  # Ollama default
LLM_API_KEY = os.getenv("LLM_API_KEY", "ollama")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))

# Simulated "hardware"
FAKE_BACKEND = "FakeBrisbane"          # offline copy of a real 127-qubit IBM device (noise model included)
HARDWARE_BUDGET_SECONDS = 600          # mirrors the real 10-minute IBM quota
SECONDS_PER_JOB_OVERHEAD = 5.0         # estimated queue/setup cost per hardware job
SECONDS_PER_SHOT = 0.01                # estimated cost per shot

# Dummy credential. NEVER put a real token here.
IBM_TOKEN = "FAKE_TOKEN_123"

# Agent loop limits
MAX_STEPS_PER_TURN = 8
MAX_MESSAGE_DEPTH = 4
