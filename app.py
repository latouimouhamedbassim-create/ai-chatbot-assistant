"""AI Chatbot Assistant - a small Flask app backed by the Anthropic API.

Features: streaming replies, per-session memory, configurable persona.
"""
import os
import uuid

from anthropic import Anthropic
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request, stream_with_context

load_dotenv()

MODEL = os.getenv("MODEL", "claude-sonnet-4-5")
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "You are a friendly, concise customer-support assistant. "
    "Answer in the user's language. If you do not know, say so.",
)
MAX_HISTORY = 20  # messages kept per session

app = Flask(__name__)
client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment
sessions: dict[str, list[dict]] = {}


@app.get("/")
def index():
    return render_template("index.html")


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
            with client.messages.stream(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=history,
            ) as stream:
                for text in stream.text_stream:
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
