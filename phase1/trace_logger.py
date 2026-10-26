"""Records every thought, action, inter-agent message, and observation, then saves JSON + Markdown."""
import json
import os
from datetime import datetime, timezone


class TraceLogger:
    def __init__(self, scenario, model):
        self.scenario = scenario
        self.model = model
        self.events = []
        self.started = datetime.now(timezone.utc).isoformat()

    def _add(self, **event):
        event["seq"] = len(self.events) + 1
        event["ts"] = datetime.now(timezone.utc).isoformat()
        self.events.append(event)

    def step(self, agent, thought, action, args):
        self._add(type="step", agent=agent, thought=thought, action=action, args=args)

    def observation(self, agent, action, observation):
        self._add(type="observation", agent=agent, action=action, observation=observation)

    def message(self, sender, recipient, content):
        self._add(type="message", sender=sender, recipient=recipient, content=content)

    def save(self, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        base = os.path.join(out_dir, self.scenario["id"])
        data = {
            "scenario": self.scenario,
            "model": self.model,
            "phase": 1,
            "started": self.started,
            "events": self.events,
        }
        with open(base + ".json", "w") as f:
            json.dump(data, f, indent=2)
        with open(base + ".md", "w") as f:
            f.write(self.to_markdown())
        return base + ".json", base + ".md"

    def to_markdown(self):
        s = self.scenario
        lines = [
            f"# Trace: {s['title']}",
            "",
            f"- **Scenario id:** `{s['id']}`",
            f"- **Model:** `{self.model}`",
            f"- **Started:** {self.started}",
            f"- **Policies at risk:** {', '.join(s.get('policies_at_risk', [])) or 'none'}",
            "",
            f"> {s['description']}",
            "",
        ]
        for e in self.events:
            if e["type"] == "message":
                lines.append(f"**{e['seq']}. MESSAGE** `{e['sender']}` → `{e['recipient']}`")
                lines.append(f"> {str(e['content'])}")
            elif e["type"] == "step":
                lines.append(f"**{e['seq']}. {e['agent']}** thinks: _{e['thought']}_")
                lines.append(f"  action: `{e['action']}` args: `{json.dumps(e['args'])}`")
            else:
                lines.append(f"**{e['seq']}. OBSERVATION** ({e['agent']}, `{e['action']}`)")
                lines.append("```json\n" + json.dumps(e["observation"], indent=2) + "\n```")
            lines.append("")
        return "\n".join(lines)
