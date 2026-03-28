from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import OpenAI
import os
import sys
import httpx
from datetime import datetime

load_dotenv()

# Allow importing auth.py from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auth

MEETSTREAM_API_KEY = os.getenv("MEETSTREAM_API_KEY")
WEBHOOK_BASE_URL   = os.getenv("WEBHOOK_BASE_URL", "")
STUB_USER_ID       = "hackathon-user"

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
    "recipient_email": "",
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

# ── Bridge posts bot lifecycle status here ──────────────────────────────────
@app.post("/internal/bot_status")
async def receive_bot_status(request: Request):
    body = await request.json()
    status = body.get("status", "unknown")
    session["bot_status"] = status
    await manager.broadcast({"type": "bot_status", "status": status})
    return {"ok": True}

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

# ── Join meeting ─────────────────────────────────────────────────────────────
@app.post("/api/join")
async def join_meeting(request: Request):
    body = await request.json()
    meeting_link = body.get("meeting_link", "").strip()
    if not meeting_link:
        return {"error": "meeting_link is required"}, 400
    if not MEETSTREAM_API_KEY:
        return {"error": "MEETSTREAM_API_KEY not set in .env"}, 500
    if not WEBHOOK_BASE_URL:
        return {"error": "WEBHOOK_BASE_URL not set in .env (start ngrok first)"}, 500

    payload = {
        "meeting_link": meeting_link,
        "video_required": False,
        "bot_name": "Hackathon Notetaker",
        "callback_url": f"{WEBHOOK_BASE_URL}/webhooks/meetstream",
        "recording_config": {
            "transcript": {
                "provider": {
                    "deepgram": {
                        "model": "nova-3",
                        "language": "en",
                        "punctuate": True,
                        "smart_format": True,
                        "diarize": True,
                    }
                }
            }
        },
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                "https://api.meetstream.ai/api/v1/bots/create_bot",
                json=payload,
                headers={"Authorization": f"Token {MEETSTREAM_API_KEY}"},
                timeout=15,
            )
            data = resp.json()
        except Exception as e:
            return {"error": f"MeetStream API error: {e}"}, 502

        if not resp.is_success:
            return {"error": data}, resp.status_code

        bot_id        = data.get("bot_id") or data.get("id")
        transcript_id = data.get("transcript_id")

        # Register mapping with webhook server (localhost:3001)
        try:
            await client.post(
                "http://localhost:3001/register_bot",
                json={"bot_id": bot_id, "transcript_id": transcript_id},
                timeout=5,
            )
        except Exception:
            pass  # Non-fatal — server may not be up yet

    session["bot_status"] = "joining"
    await manager.broadcast({"type": "bot_status", "status": "joining"})
    return {"ok": True, "bot_id": bot_id}


# ── Gmail auth status ─────────────────────────────────────────────────────────
@app.get("/api/gmail-status")
async def gmail_status():
    try:
        authorized = auth.is_authorized(STUB_USER_ID, connection_name="gmail")
        if authorized:
            return {"authorized": True}
        link = auth.get_auth_link(STUB_USER_ID, connection_name="gmail")
        return {"authorized": False, "auth_link": link}
    except Exception as e:
        return {"authorized": False, "error": str(e)}


# ── Recipient email ──────────────────────────────────────────────────────────
@app.post("/api/set-recipient")
async def set_recipient(request: Request):
    body = await request.json()
    email = body.get("email", "").strip()
    session["recipient_email"] = email
    return {"ok": True}

# ── Generate summary ─────────────────────────────────────────────────────────
@app.post("/api/summarize")
async def summarize():
    if not session["transcript"]:
        return {"summary": "No transcript yet."}

    full_text = "\n".join(
        f"{e['speaker']}: {e['text']}" for e in session["transcript"]
    )

    try:
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
    except Exception as e:
        msg = str(e)
        if "401" in msg or "invalid_api_key" in msg or "Incorrect API key" in msg:
            return {"error": "Invalid OpenAI API key. Update OPENAI_API_KEY in .env and restart the backend."}, 400
        return {"error": f"OpenAI error: {msg}"}, 500

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

    try:
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
    except Exception as e:
        msg = str(e)
        if "401" in msg or "invalid_api_key" in msg or "Incorrect API key" in msg:
            return {"error": "Invalid OpenAI API key. Update OPENAI_API_KEY in .env and restart the backend."}, 400
        return {"error": f"OpenAI error: {msg}"}, 500

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

