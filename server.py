import json
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from transcript import fetch_transcript
import dispatcher

app = FastAPI()

# In-memory bot_id -> transcript_id mapping, populated by send_bot.py via /register_bot
bot_transcript_map: dict[str, str] = {}


def log(prefix: str, msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] [{prefix}] {msg}")


@app.post("/webhooks/meetstream")
async def meetstream_webhook(request: Request) -> JSONResponse:
    payload = await request.json()
    event_type = payload.get("event", "unknown")

    log("WEBHOOK", f"Received event: {event_type}")

    if event_type == "bot.joining":
        log("WEBHOOK", "Bot is connecting...")
    elif event_type == "bot.inmeeting":
        log("WEBHOOK", "Bot is live and recording")
    elif event_type == "bot.stopped":
        log("WEBHOOK", "Meeting ended, waiting for transcript...")
    elif event_type == "transcription.processed":
        # Log full payload so we can confirm field names from the real response
        log("WEBHOOK", f"transcription.processed full payload: {json.dumps(payload, indent=2)}")
        bot_id = payload.get("data", {}).get("bot_id") or payload.get("bot_id")
        transcript_id = bot_transcript_map.get(bot_id)
        if not transcript_id:
            log("WEBHOOK", f"No transcript_id registered for bot_id={bot_id}, cannot fetch transcript")
        else:
            log("WEBHOOK", f"Resolved transcript_id={transcript_id} for bot_id={bot_id}, fetching...")
            transcript = await fetch_transcript(transcript_id)
            print(json.dumps(transcript, indent=2))
            # TODO: swap {} for real extraction output once Person 2 is ready
            # e.g. extraction = await extract_actions(transcript)
            await dispatcher.dispatch({})
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
    uvicorn.run("server:app", host="0.0.0.0", port=3001, reload=True)
