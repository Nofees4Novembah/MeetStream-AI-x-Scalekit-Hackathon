# MeetStream AI x Scalekit

A post-meeting action agent. A bot joins your meeting, records it, and when it ends: transcribes everything, generates a summary, sends a follow-up email via Gmail, and creates calendar events for action items.

---

## How it works

```
Dashboard (port 3002)
  └─ paste meeting link → "Send bot"
       └─ Backend (port 3000) → MeetStream API → bot joins meeting
            └─ Webhook server (port 3001) receives lifecycle events
                 └─ on meeting end: fetches transcript → runs connectors
                      ├─ Gmail: sends follow-up email
                      └─ Google Calendar: creates events for action items

Bridge (port 8000) — real-time AI voice agent inside the meeting
```

---

## Starting everything

Double-click **`start.bat`** — opens all 5 services in labeled terminal windows.

After ngrok opens:
1. Copy the `https://xxxx.ngrok.io` URL from the ngrok window
2. Paste it into `.env` as `WEBHOOK_BASE_URL`
3. Close and reopen the **Webhook Server :3001** window (it reads the URL on startup)

---

## .env checklist

```
MEETSTREAM_API_KEY=         # MeetStream dashboard
WEBHOOK_BASE_URL=           # set after ngrok starts
SCALEKIT_ENV_URL=           # Scalekit dashboard
SCALEKIT_CLIENT_ID=         # Scalekit dashboard
SCALEKIT_CLIENT_SECRET=     # Scalekit dashboard
OPENAI_API_KEY=             # platform.openai.com/api-keys
BACKEND_URL=http://localhost:3000
```

---

## Testing the demo

1. Run `start.bat`, set `WEBHOOK_BASE_URL`, restart the webhook server window
2. Open `http://localhost:3002`
3. Click **Connect Gmail** in the sidebar and authorize via the Scalekit OAuth flow
4. Paste a Google Meet link into **Join a meeting** and click **Send bot**
5. Talk in the meeting — transcript appears live in the dashboard
6. End the meeting — bot leaves, transcript is fetched, Gmail follow-up fires automatically
7. Click **Generate summary** for a GPT-4o summary
8. Type a name and click **Generate brief** for a late-joiner catchup

> Google Meet works out of the box. Zoom requires Zoom OAuth configured in the MeetStream dashboard.

---

## What works

| Feature | Status |
|---|---|
| Send bot from dashboard | Working |
| Bot status updates (joining / inmeeting / stopped) | Working |
| Live transcript in dashboard | Working |
| Generate summary (GPT-4o) | Working — needs `OPENAI_API_KEY` |
| Late joiner brief (GPT-4o) | Working — needs `OPENAI_API_KEY` |
| Connect Gmail from dashboard | Working |
| Gmail follow-up email | Working — needs Gmail connected |
| Real-time in-meeting AI agent (bridge) | Working — needs `OPENAI_API_KEY` |
| Google Calendar event creation | Stub — needs `execute_tool` call filled in |
| Post-call action item extraction | Stub — dispatcher receives `{}` until wired in |

---

## What still needs to be done

### 1. Wire in action item extraction

`server.py` currently passes `{}` to the dispatcher. Swap it out once an extraction function exists:

```python
# In server.py, replace:
await dispatcher.dispatch({})

# With:
from extraction import extract_actions
extraction = await extract_actions(transcript)
await dispatcher.dispatch(extraction)
```

Expected shape (connectors use `.get()` so partial is fine):

```python
{
    "summary": "str",
    "action_items": [{"title": "str", "owner": "str", "due": "str"}],
    "recipient_email": "str",
    "recipient_name": "str",
    "participants": ["str"]
}
```

Use `sample_transcript.json` (project root) to build and test the prompt.

### 2. Finish Google Calendar connector

`connectors/google_calendar.py` has auth but no API call. Follow the Gmail pattern:

```python
actions = auth.get_actions()
result = actions.execute_tool(
    tool_name="googlecalendar_create_event",  # confirm exact name in Scalekit dashboard
    identifier=STUB_USER_ID,
    tool_input={
        "title": item.get("title"),
        "start": item.get("due"),
    },
)
```

Check **Scalekit dashboard → Agent Auth → Tools** for the exact `tool_name` and input schema.

### 3. Nice to have

- Replace `STUB_USER_ID = "hackathon-user"` in connectors with a real user identity from the dashboard
- Persist `bot_id → transcript_id` mapping to a file so server restarts don't lose it
- Add more connectors (Slack, HubSpot) — just drop a file in `connectors/`, no other changes needed

---

## Adding a connector

Drop a file in `connectors/` with an `async def run(extraction: dict)` function. The dispatcher picks it up automatically.

```python
# connectors/slack.py
async def run(extraction: dict) -> None:
    ...
```

---

## File map

```
start.bat                  ← double-click to start all 5 services
server.py                  ← webhook server (port 3001)
transcript.py              ← fetches transcript from MeetStream after meeting ends
send_bot.py                ← CLI fallback: uv run python send_bot.py "<link>"
auth.py                    ← Scalekit client + OAuth helpers
dispatcher.py              ← auto-discovers and runs all connectors concurrently
connectors/
  gmail_followup.py        ← sends follow-up email via Gmail API
  google_calendar.py       ← stub — needs execute_tool call
  hubspot.py               ← stub
  slack.py                 ← stub
backend/
  main.py                  ← dashboard backend (port 3000), WebSocket, GPT-4o, join/auth endpoints
dashboard/                 ← Next.js frontend (port 3002)
app/
  server.py                ← real-time bridge to OpenAI Realtime API (port 8000)
sample_transcript.json     ← real transcript sample for testing extraction
.env.example               ← copy to .env and fill in
```
