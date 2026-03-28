# Project Status

Last updated: 2026-03-28

---

## What's built and working

### MeetStream pipeline (fully working)

`send_bot.py` → MeetStream API → bot joins meeting → webhooks fire → `server.py` handles them → transcript fetched → saved to `sample_transcript.json`

**Files:**
- `send_bot.py` — CLI to dispatch a bot: `uv run python send_bot.py "https://meet.google.com/xxx"`
- `server.py` — FastAPI on port 3001, handles all lifecycle webhooks
- `transcript.py` — fetches structured + raw transcript, saves to `sample_transcript.json`

**Webhook event flow:**
```
bot.joining          → "Bot is connecting..."
bot.inmeeting        → "Bot is live and recording"
bot.stopped          → "Meeting ended, waiting for transcript..."
transcription.processed → fetches transcript → runs dispatcher
```

**The bot_id / transcript_id quirk:**
MeetStream's `transcription.processed` webhook only includes `bot_id`, not `transcript_id`. We work around this by having `send_bot.py` POST the mapping to `/register_bot` immediately after creating the bot. The server stores it in memory and uses it when the webhook arrives. If the server restarts between bot creation and meeting end, the mapping is lost — fine for a hackathon.

**Endpoints:**
- `POST /webhooks/meetstream` — MeetStream calls this (don't call directly)
- `POST /register_bot` — called by `send_bot.py` to register `bot_id → transcript_id`
- `GET /health` — returns `{"status": "ok"}`

---

### Scalekit auth (built, needs connector-level testing)

`auth.py` wraps the Scalekit SDK with helpers for any connection type:

```python
connect_user(user_id, connection_name="googlecalendar")
get_auth_link(user_id, connection_name="googlecalendar")
is_authorized(user_id, connection_name="googlecalendar")
ensure_authorized(user_id, connection_name="googlecalendar")
get_actions()  # returns ScalekitClient.actions for execute_tool() calls
```

Pass `connection_name="gmail"` for Gmail, `"googlecalendar"` for Calendar (default).

---

### Connector architecture (built, stubs need filling in)

`dispatcher.py` auto-discovers every file in `connectors/` that has an `async def run(extraction: dict)` function and runs them all concurrently. **Nobody touches `dispatcher.py` to add a connector** — just drop a new file in `connectors/`.

**Connectors:**

| File | Status | Notes |
|---|---|---|
| `connectors/google_calendar.py` | Stub | Auth check done. `execute_tool` call not yet implemented. |
| `connectors/gmail_followup.py` | Implemented | Builds email body, calls `execute_tool(tool_name="gmail_send_email", ...)`. Needs live test. |

**Adding a connector** (e.g. Slack):
```python
# connectors/slack.py
async def run(extraction: dict) -> None:
    ...  # dispatcher picks this up automatically
```

---

### Gmail connector (implemented, needs auth + live test)

`connectors/gmail_followup.py` — sends a post-meeting summary email via Scalekit's Gmail proxy.

- Checks Gmail auth via `ensure_authorized()`
- Builds a plain-text email from `extraction` fields
- Sends via `actions.execute_tool(tool_name="gmail_send_email", ...)`

**To test:**
1. Fill in `recipient_email` in `test_gmail.py`
2. Run `uv run python test_gmail.py`
3. First run will print a Gmail OAuth link — open it, authorize, re-run

---

## What's not done yet

### 1. Person 2 — LLM extraction (blocking everything downstream)

`server.py` currently passes an empty `{}` to `dispatcher.dispatch()`. The connectors only do real work once extraction is wired in.

The hook is already in place in `server.py`:
```python
transcript = await fetch_transcript(transcript_id)
# TODO: swap {} for real extraction output once Person 2 is ready
# e.g. extraction = await extract_actions(transcript)
await dispatcher.dispatch({})
```

**When Person 2 is ready**, the only change needed in `server.py` is:
```python
from extraction import extract_actions
...
extraction = await extract_actions(transcript)
await dispatcher.dispatch(extraction)
```

**Expected extraction schema** (not finalised — connectors use `.get()` with fallbacks):
```python
{
    "summary": "str",
    "action_items": [
        {"title": "str", "owner": "str", "due": "str"}
    ],
    "recipient_email": "str",
    "recipient_name": "str",
    "participants": ["str"]
}
```

`sample_transcript.json` in the project root has a real transcript to build the prompt against.

---

### 2. Google Calendar connector (partial)

`connectors/google_calendar.py` has the auth check but the actual `execute_tool` call isn't implemented. Needs the same pattern as the Gmail connector:

```python
actions = auth.get_actions()
result = actions.execute_tool(
    tool_name="googlecalendar_create_event",  # confirm tool name in Scalekit dashboard
    identifier=STUB_USER_ID,
    tool_input={
        "title": item.get("title"),
        "due": item.get("due"),
        # ... whatever fields the tool expects
    },
)
```

Check the Scalekit dashboard for the exact `tool_name` — it follows the pattern `googlecalendar_<action>`.

---

### 3. Real user identity (currently hardcoded)

Both connectors use `STUB_USER_ID = "hackathon-user"`. Once Person 4's dashboard is in place, the user identity should be passed through so each user connects their own Google account.

---

### 4. Person 4 — Streamlit dashboard (not started)

Nothing exists yet. Useful hooks already available:
- `GET /health` to check server status
- `POST /register_bot` response includes `bot_id` — can track active bots
- Add `GET /status/{bot_id}` to `server.py` to expose pipeline state (bot status, transcript ready, extraction done)
- `send_bot.py` logic can be imported directly or called as subprocess

---

## How to run

```bash
# 1. Fill in .env (copy from .env.example, add MEETSTREAM_API_KEY + Scalekit creds)

# 2. Start the server
uv run python server.py

# 3. Start ngrok (separate terminal)
ngrok http 3001

# 4. Paste ngrok URL into .env as WEBHOOK_BASE_URL, restart server

# 5. Send a bot to a meeting
uv run python send_bot.py "https://meet.google.com/xxx-xxxx-xxx"

# 6. Test Gmail connector standalone
uv run python test_gmail.py
```

---

## File map

```
server.py                  ← webhook server (port 3001)
transcript.py              ← transcript fetcher
send_bot.py                ← CLI to dispatch a bot
auth.py                    ← Scalekit client + OAuth helpers
dispatcher.py              ← auto-discovers and runs all connectors
connectors/
  base.py                  ← Connector protocol (documents the interface)
  google_calendar.py       ← stub — needs execute_tool call
  gmail_followup.py        ← implemented — needs live test
test_gmail.py              ← standalone Gmail test script
sample_transcript.json     ← real transcript output (for Person 2)
INTEGRATION.md             ← integration guide for all teammates
SCALEKIT_TEAMMATE_BRIEF.md ← brief for Person 3 to upload to Claude
.env.example               ← copy to .env and fill in
```
