"""AI Chatbot Assistant - a small Flask app backed by the Anthropic API.

Features: streaming replies, per-session memory, configurable persona,
and a keyless DEMO MODE (scripted replies) so anyone can try the UI instantly.
"""
import os
import re
import time
import uuid

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request, stream_with_context

from demo_replies import demo_reply

load_dotenv()

MODEL = os.getenv("MODEL", "claude-sonnet-4-5")
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "You are a friendly, concise customer-support assistant. "
    "Answer in the user's language. If you do not know, say so.",
)
MAX_HISTORY = 20  # messages kept per session

# Demo mode: forced with DEMO_MODE=1, or automatic when no API key is configured.
DEMO_MODE = os.getenv("DEMO_MODE") == "1" or not os.getenv("ANTHROPIC_API_KEY")

app = Flask(__name__)
client = None
if not DEMO_MODE:
    from anthropic import Anthropic

    client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment

sessions: dict[str, list[dict]] = {}


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/info")
def info():
    return jsonify(demo=DEMO_MODE, model=None if DEMO_MODE else MODEL)


def stream_demo(message: str):
    """Yield a scripted reply word by word, like a real streaming model."""
    for word in re.findall(r"\S+\s*", demo_reply(message)):
        time.sleep(0.03)
        yield word


def stream_claude(history: list[dict]):
    with client.messages.stream(
        model=MODEL, max_tokens=1024, system=SYSTEM_PROMPT, messages=history
    ) as stream:
        yield from stream.text_stream


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify(error="Message is required"), 400

    session_id = data.get("session_id") or str(uuid.uuid4())
    history = sessions.setdefault(session_id, [])
    history.append({"role": "user", "content": message})
    del history[:-MAX_HISTORY]

    def generate():
        reply = ""
        try:
            source = stream_demo(message) if DEMO_MODE else stream_claude(history)
            for text in source:
                reply += text
                yield text
        except Exception as exc:  # surface errors to the UI instead of a blank reply
            yield f"\n[error] {exc}"
            history.pop()
            return
        history.append({"role": "assistant", "content": reply})

    return Response(
        stream_with_context(generate()),
        mimetype="text/plain",
        headers={"X-Session-Id": session_id},
    )


@app.post("/api/reset")
def reset():
    sessions.pop((request.get_json(silent=True) or {}).get("session_id", ""), None)
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1", port=int(os.getenv("PORT", 5000)))
