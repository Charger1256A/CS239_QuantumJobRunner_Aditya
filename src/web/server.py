"""Local demo website: type a request and watch the agents talk, live.

  cd src && python -m web.server          # then open http://localhost:8000

Runs the real Phase 1 agents and streams each trace event to the browser with
Server-Sent Events. When the Planner calls ask_user, the page shows a prompt and
the run waits for your answer. Standard library only (no extra dependencies).
"""
import argparse
import json
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from phase1 import config
from phase1.agents import build_agents
from phase1.llm import OpenAICompatibleLLM
from phase1.orchestrator import Orchestrator
from phase1.quantum_lab import QuantumLab
from phase1.trace_logger import TraceLogger

STATIC_DIR = Path(__file__).parent / "static"
SCENARIO_DIR = Path(__file__).parent.parent / "phase1" / "scenarios"
TRACE_DIR = Path(__file__).parent.parent / "traces"
ASK_USER_TIMEOUT = 300  # seconds to wait for an answer before treating the user as unavailable

SESSIONS = {}


class Session:
    """One live run. Holds the event list that browsers stream from, plus the pending ask_user answer."""

    def __init__(self, request):
        self.id = uuid.uuid4().hex[:8]
        self.request = request
        self.events = []
        self.done = False
        self.cond = threading.Condition()
        self.answer = None
        self.answer_ready = threading.Event()

    def push(self, event):
        with self.cond:
            self.events.append(event)
            self.cond.notify_all()

    def finish(self, event):
        with self.cond:
            self.events.append(event)
            self.done = True
            self.cond.notify_all()


class StreamingLogger(TraceLogger):
    """TraceLogger that also pushes each event to the browser as it happens."""

    def __init__(self, scenario, model, session):
        super().__init__(scenario, model)
        self.session = session

    def _add(self, **event):
        super()._add(**event)
        self.session.push(json.loads(json.dumps(self.events[-1], default=str)))


def run_session(session):
    scenario = {"id": f"web_{session.id}", "title": "Web demo request",
                "description": "Request typed into the demo website.",
                "user_request": session.request, "user_replies": [], "policies_at_risk": []}
    try:
        llm = OpenAICompatibleLLM()
        logger = StreamingLogger(scenario, llm.model, session)

        def ask_user(question):
            logger.message("Planner", "User", question)
            session.answer_ready.clear()
            session.push({"type": "ask_user", "question": question})
            if session.answer_ready.wait(ASK_USER_TIMEOUT):
                answer = session.answer
            else:
                answer = "(no answer: user is unavailable)"
            logger.message("User", "Planner", answer)
            return {"user_answer": answer}

        agents = build_agents(QuantumLab(), llm, logger, ask_user)
        final = Orchestrator(agents, logger).run(session.request)
        json_path, _ = logger.save(TRACE_DIR / "web")
        session.finish({"type": "done", "final": final, "trace": str(Path(json_path).relative_to(TRACE_DIR.parent))})
    except Exception as e:  # e.g. the LLM server is not running
        session.finish({"type": "error", "error": f"{type(e).__name__}: {e}"})


def recorded_traces():
    out = []
    for f in sorted(TRACE_DIR.glob("*/*.json")):
        data = json.loads(f.read_text())
        out.append({"id": f"{f.parent.name}/{f.stem}", "title": data["scenario"].get("title", f.stem),
                    "request": data["scenario"].get("user_request", ""), "model": data.get("model")})
    return out


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # keep the terminal quiet
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            return self._send(200, (STATIC_DIR / "index.html").read_bytes(), "text/html; charset=utf-8")
        if path == "/api/info":
            return self._send(200, {"model": config.LLM_MODEL, "base_url": config.LLM_BASE_URL,
                                    "budget": config.HARDWARE_BUDGET_SECONDS})
        if path == "/api/scenarios":
            items = [json.loads(f.read_text()) for f in sorted(SCENARIO_DIR.glob("*.json"))]
            return self._send(200, [{"id": s["id"], "title": s["title"], "request": s["user_request"]} for s in items])
        if path == "/api/traces":
            return self._send(200, recorded_traces())
        if path.startswith("/api/traces/"):
            rel = path[len("/api/traces/"):]
            f = (TRACE_DIR / f"{rel}.json").resolve()
            if TRACE_DIR.resolve() not in f.parents or not f.exists():
                return self._send(404, {"error": "no such trace"})
            return self._send(200, f.read_bytes())
        if path.startswith("/api/stream/"):
            return self._stream(path.rsplit("/", 1)[-1])
        self._send(404, {"error": "not found"})

    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/api/run":
            request = str(self._body().get("request", "")).strip()
            if not request:
                return self._send(400, {"error": "empty request"})
            session = Session(request)
            SESSIONS[session.id] = session
            threading.Thread(target=run_session, args=(session,), daemon=True).start()
            return self._send(200, {"session": session.id})
        if path.startswith("/api/answer/"):
            session = SESSIONS.get(path.rsplit("/", 1)[-1])
            if session is None:
                return self._send(404, {"error": "no such session"})
            session.answer = str(self._body().get("answer", ""))
            session.answer_ready.set()
            return self._send(200, {"ok": True})
        self._send(404, {"error": "not found"})

    def _stream(self, sid):
        session = SESSIONS.get(sid)
        if session is None:
            return self._send(404, {"error": "no such session"})
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        sent = 0
        try:
            while True:
                with session.cond:
                    while sent == len(session.events) and not session.done:
                        if not session.cond.wait(15):
                            break
                    batch = session.events[sent:]
                    finished = session.done
                if not batch and not finished:
                    self.wfile.write(b": keepalive\n\n")  # stops proxies/browsers from timing out
                for e in batch:
                    self.wfile.write(f"data: {json.dumps(e, default=str)}\n\n".encode())
                sent += len(batch)
                self.wfile.flush()
                if finished and sent == len(session.events):
                    return
        except (BrokenPipeError, ConnectionResetError):
            return


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8000)
    a = p.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(f"Quantum Job Runner demo: http://localhost:{a.port}  (model {config.LLM_MODEL} at {config.LLM_BASE_URL})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
