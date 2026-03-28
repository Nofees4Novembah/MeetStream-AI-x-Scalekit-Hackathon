from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import OpenAI
import os
from datetime import datetime

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── In-memory store ──────────────────────────────────────────────────────────
session = {
    "bot_status": "waiting",
    "transcript": [],
    "summary": "",
    "word_count": 0,
    "start_time": None,
}

# ── WebSocket manager ────────────────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)

manager = ConnectionManager()

# ── Dashboard connects here ──────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    await ws.send_json({"type": "init", "data": session})
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)

# ── Bridge posts transcript chunks here ─────────────────────────────────────
@app.post("/internal/transcript")
async def receive_transcript(request: Request):
    chunk = await request.json()

    words = chunk.get("words", [])
    avg_confidence = (
        sum(w.get("confidence", 1.0) for w in words) / len(words)
        if words else 1.0
    )

    entry = {
        "speaker":         chunk.get("speakerName", "Unknown"),
        "timestamp":       chunk.get("timestamp", datetime.utcnow().isoformat()),
        "text":            chunk.get("transcript", ""),
        "confidence":      round(avg_confidence, 2),
        "words":           words,
        "flag_for_review": avg_confidence < 0.70,
    }

    session["transcript"].append(entry)
    session["word_count"] += len(entry["text"].split())

    if session["start_time"] is None:
        session["start_time"] = entry["timestamp"]
        session["bot_status"] = "inmeeting"

    await manager.broadcast({
        "type":       "transcript",
        "entry":      entry,
        "word_count": session["word_count"],
    })

    return {"ok": True}

# ── Generate summary ─────────────────────────────────────────────────────────
@app.post("/api/summarize")
async def summarize():
    if not session["transcript"]:
        return {"summary": "No transcript yet."}

    full_text = "\n".join(
        f"{e['speaker']}: {e['text']}" for e in session["transcript"]
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=500,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful meeting assistant that summarizes transcripts clearly and concisely.",
            },
            {
                "role": "user",
                "content": (
                    "Summarize this meeting transcript in 3-4 sentences, "
                    "then list any action items.\n\n" + full_text
                ),
            },
        ],
    )

    summary = response.choices[0].message.content
    session["summary"] = summary
    await manager.broadcast({"type": "summary", "summary": summary})
    return {"summary": summary}

# ── Late joiner brief ────────────────────────────────────────────────────────
@app.post("/api/late-joiner-brief")
async def late_joiner_brief(request: Request):
    body = await request.json()
    name = body.get("name", "New participant")

    if not session["transcript"]:
        return {"brief": "The meeting just started — nothing to catch up on yet."}

    full_text = "\n".join(
        f"{e['speaker']}: {e['text']}" for e in session["transcript"]
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=200,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful meeting assistant that writes brief, clear catchups for late joiners.",
            },
            {
                "role": "user",
                "content": (
                    f"{name} just joined the meeting late. "
                    "Write a 2-3 sentence catchup they can read in 10 seconds.\n\n"
                    "Transcript so far:\n" + full_text
                ),
            },
        ],
    )

    return {"brief": response.choices[0].message.content}

# ── Flagged items for human review ───────────────────────────────────────────
@app.get("/api/flagged")
async def get_flagged():
    flagged = [e for e in session["transcript"] if e.get("flag_for_review")]
    return {"flagged": flagged, "count": len(flagged)}

# ── Session state ────────────────────────────────────────────────────────────
@app.get("/api/session")
async def get_session():
    return session