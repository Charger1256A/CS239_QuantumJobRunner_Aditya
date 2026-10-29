"""LLM clients and action parsing.

Agents must answer with one JSON object:
  {"thought": "...", "action": "<tool or special action>", "args": {...}}
"""
import json
import re

from . import config


class OpenAICompatibleLLM:
    """Works with Ollama, LM Studio, vLLM, OpenAI, or any OpenAI-compatible server."""

    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(base_url=config.LLM_BASE_URL, api_key=config.LLM_API_KEY)
        self.model = config.LLM_MODEL

    def chat(self, messages, agent=None):
        resp = self.client.chat.completions.create(
            model=self.model, messages=messages, temperature=config.LLM_TEMPERATURE
        )
        return resp.choices[0].message.content or ""


class ScriptedLLM:
    """Replays canned responses per agent. Used only for offline smoke tests, never for submitted traces."""

    model = "scripted-test-llm"

    def __init__(self, responses_by_agent):
        self.queues = {k: list(v) for k, v in responses_by_agent.items()}

    def chat(self, messages, agent=None):
        q = self.queues.get(agent, [])
        if not q:
            return json.dumps({"thought": "Script exhausted.", "action": "reply", "args": {"content": "(done)"}})
        item = q.pop(0)
        return item if isinstance(item, str) else json.dumps(item)


def parse_action(raw):
    """Pull the first JSON object out of the model output. Falls back to a plain reply."""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start = text.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(text[start : i + 1], strict=False)
                        obj.setdefault("thought", "")
                        obj.setdefault("args", {})
                        if not isinstance(obj["args"], dict):
                            obj["args"] = {}
                        return obj
                    except json.JSONDecodeError:
                        break
    return {"thought": "(unparseable output, treated as reply)", "action": "reply", "args": {"content": raw}}
