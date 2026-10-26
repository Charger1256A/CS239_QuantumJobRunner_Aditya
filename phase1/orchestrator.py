"""Routes messages between agents and the user. Phase 1: no policy checks on any message."""
from . import config


class Orchestrator:
    def __init__(self, agents, logger):
        self.agents = agents
        self.logger = logger

    def deliver(self, sender, recipient, content, depth):
        self.logger.message(sender, recipient, content)
        if recipient not in self.agents:
            return {"error": f"unknown agent '{recipient}'"}
        if depth > config.MAX_MESSAGE_DEPTH:
            return {"error": "message depth limit reached"}
        reply = self.agents[recipient].handle(sender, content, self, depth)
        self.logger.message(recipient, sender, reply)
        return {"reply_from": recipient, "content": reply}

    def run(self, user_request):
        return self.deliver("User", "Planner", user_request, depth=0)["content"]
