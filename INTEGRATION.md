# Integration Guide

This document is for teammates integrating with the webhook server. Read this before touching `server.py`.

## What this server does

FastAPI server that:
1. Sends a MeetStream bot into a meeting (`send_bot.py`)
2. Receives bot lifecycle webhooks from MeetStream
3. Fetches the full post-call transcript when transcription is ready

Runs on port **3001**, exposed publicly via ngrok.

---

## Endpoints

### `POST /webhooks/meetstream`
MeetStream calls this automatically for bot lifecycle events. **You don't call this directly.**

Events handled: `bot.joining`, `bot.inmeeting`, `bot.stopped`, `transcription.processed`

### `POST /register_bot`
Called automatically by `send_bot.py` after creating a bot. Stores the `bot_id → transcript_id` mapping so the server can fetch the right transcript when the webhook arrives.

```json
{ "bot_id": "...", "transcript_id": "..." }
```

Returns `{"registered": true}`

### `GET /health`
Returns `{"status": "ok"}`

---

## Transcript data shape

The transcript is a **JSON array of segment objects**. Each segment is one continuous speech turn by a speaker.

```json
[
  {
    "speaker": "Quinn",
    "transcript": "I've had to test some blank data for Nafis to do something with it.",
    "start_time": 0.0,
    "end_time": 42.47,
    "words": [
      {
        "word": "i've",
        "start": 0.0,
        "end": 1.04,
        "confidence": 0.35,
        "speaker": 0,
        "speaker_confidence": 0.14,
        "punctuated_word": "I've"
      }
    ]
  }
]
```

**Field reference:**

| Field | Type | Notes |
|---|---|---|
| `speaker` | string | Speaker name (from Deepgram diarization) |
| `transcript` | string | Full text of the speech segment |
| `start_time` | float | Seconds from start of recording |
| `end_time` | float | Seconds from start of recording |
| `words` | array | Word-level data (see below) |

**Word-level fields** (`words` array):

| Field | Type | Notes |
|---|---|---|
| `word` | string | Lowercase word |
| `punctuated_word` | string | Word with punctuation |
| `start` / `end` | float | Timing in seconds |
| `confidence` | float | 0–1 transcription confidence |
| `speaker` | int | Speaker index (0, 1, 2…) |
| `speaker_confidence` | float | 0–1 diarization confidence |

A real sample is in `sample_transcript.json` at the project root.

---

## How to integrate — Person 2 (LLM extraction)

**Simplest path:** add your extraction module and Quinn will wire it in.

The `transcription.processed` handler in `server.py` already fetches the transcript as a Python `list[dict]`. After fetching, it currently just prints it. Add your function there:

```python
# In server.py, after transcript is fetched:
from extraction import extract_actions
result = await extract_actions(transcript)
```

Your function signature should be:
```python
async def extract_actions(transcript: list[dict]) -> dict:
    ...
```

**For offline prompt development:** use `sample_transcript.json`. The fields you actually need are just `speaker` and `transcript` — word-level data is available but not necessary for action item extraction.

---

## How to integrate — Person 3 (Scalekit actions)

Your code runs after Person 2's extraction returns structured data. You'll receive whatever dict schema Person 2 defines — expected to include action items, owners, deal context, email drafts, etc.

You can develop independently using mock extraction output and wire in once Person 2's schema is settled.

---

## How to integrate — Person 4 (Streamlit dashboard)

- Poll `GET /health` to check if server is up
- `POST /register_bot` is a good hook for tracking active bots — you could extend the payload with additional metadata
- To expose pipeline state (bot status, transcript ready, extraction done): ask Quinn to add a `GET /status/{bot_id}` endpoint or a WebSocket
- `send_bot.py` logic can be imported directly or called as a subprocess
- **Important:** `WEBHOOK_BASE_URL` in `.env` must be set to the ngrok URL before sending bots — the dashboard needs to handle this or prompt the user

---

## Running the server

```bash
# 1. Fill in MEETSTREAM_API_KEY in .env
cp .env.example .env

# 2. Start server
uv run python server.py

# 3. In another terminal, start ngrok
ngrok http 3001

# 4. Copy ngrok HTTPS URL into .env as WEBHOOK_BASE_URL, restart server

# 5. Send a bot to a meeting
uv run python send_bot.py "https://meet.google.com/xxx-xxxx-xxx"
```

---

## Important notes

- **Google Meet** works out of the box. **Zoom** requires Zoom OAuth credentials configured in the MeetStream dashboard.
- **Deepgram API key** is configured in the MeetStream dashboard — not in our `.env`.
- **ngrok free tier** changes URL on restart. Keep ngrok running; only restart the server when needed.
- **In-memory mapping:** the `bot_id → transcript_id` map lives in RAM. If the server restarts between bot creation and meeting end, the mapping is lost and the transcript won't be fetched. Fine for hackathon purposes.
- **Transcription** uses Deepgram nova-3 with `diarize=true` for speaker labeling.
