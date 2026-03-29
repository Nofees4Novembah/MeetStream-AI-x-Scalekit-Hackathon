import json
import os
from datetime import datetime, timezone

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from transcript import fetch_transcript
from extraction import extract_actions
import dispatcher

app = FastAPI()

# In-memory bot_id -> transcript_id mapping, populated by send_bot.py via /register_bot
bot_transcript_map: dict[str, str] = {}

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3000")


def log(prefix: str, msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] [{prefix}] {msg}")


async def push_status(status: str) -> None:
    """Tell the dashboard backend what the bot is currently doing."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{BACKEND_URL}/internal/bot_status", json={"status": status})
    except Exception as e:
        log("SERVER", f"Could not update backend status: {e}")


async def push_transcript(transcript: list) -> None:
    """Forward each transcript segment to the dashboard backend."""
    async with httpx.AsyncClient() as client:
        for segment in transcript:
            payload = {
                "speakerName": segment.get("speaker", "Unknown"),
                "transcript":  segment.get("transcript", ""),
                "timestamp":   segment.get("absolute_start_time") or segment.get("start_time") or 0,
                "words":       segment.get("words", []),
            }
            try:
                await client.post(f"{BACKEND_URL}/internal/transcript", json=payload)
            except Exception as e:
                log("SERVER", f"Could not push segment to backend: {e}")


@app.post("/webhooks/meetstream")
async def meetstream_webhook(request: Request) -> JSONResponse:
    payload = await request.json()
    event_type = payload.get("event", "unknown")

    log("WEBHOOK", f"Received event: {event_type}")

    if event_type == "bot.joining":
        log("WEBHOOK", "Bot is connecting...")
        await push_status("joining")
    elif event_type == "bot.inmeeting":
        log("WEBHOOK", "Bot is live and recording")
        await push_status("inmeeting")
    elif event_type == "bot.stopped":
        log("WEBHOOK", "Meeting ended, waiting for transcript...")
        await push_status("stopped")
    elif event_type == "transcription.processed":
        log("WEBHOOK", f"transcription.processed full payload: {json.dumps(payload, indent=2)}")
        data = payload.get("data", {})
        bot_id = data.get("bot_id") or payload.get("bot_id")

        # Prefer transcript_id from the payload itself; fall back to the in-memory map.
        # This makes dispatch resilient to server restarts that wipe the map.
        transcript_id = (
            data.get("transcript_id")
            or payload.get("transcript_id")
            or bot_transcript_map.get(bot_id)
        )

        if not transcript_id:
            log("WEBHOOK", f"No transcript_id found for bot_id={bot_id} — payload keys: {list(data.keys())}")
        else:
            log("WEBHOOK", f"Fetching transcript_id={transcript_id} for bot_id={bot_id}")
            transcript = await fetch_transcript(transcript_id)
            await push_transcript(transcript)
            extraction = await extract_actions(transcript)
            # Pull recipient email set via dashboard
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"{BACKEND_URL}/api/session", timeout=5)
                    recipient_email = resp.json().get("recipient_email", "")
                    if recipient_email:
                        extraction["recipient_email"] = recipient_email
            except Exception:
                pass
            await dispatcher.dispatch(extraction)
    else:
        log("WEBHOOK", f"Unhandled event type '{event_type}': {json.dumps(payload)}")

    # Always return 200 immediately — MeetStream retries on non-200 responses
    return JSONResponse(content={"received": True}, status_code=200)


@app.post("/register_bot")
async def register_bot(request: Request) -> JSONResponse:
    body = await request.json()
    bot_id = body.get("bot_id")
    transcript_id = body.get("transcript_id")
    bot_transcript_map[bot_id] = transcript_id
    log("WEBHOOK", f"Registered bot_id={bot_id} -> transcript_id={transcript_id}")
    return JSONResponse(content={"registered": True})


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse(content={"status": "ok"})


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=3001, reload=False)
