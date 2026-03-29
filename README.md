# MeetStream AI x Scalekit

A post-meeting action agent. A bot joins your meeting, records it, and when it ends: transcribes everything, extracts action items with GPT-4o, sends a follow-up email via Gmail, and creates Google Calendar events.

---

## How it works

```
Dashboard (port 3002)
  └─ paste meeting link + recipient email → "Send bot"
       └─ Backend (port 3000) → MeetStream API → bot joins meeting
            └─ Webhook server (port 3001) receives lifecycle events
                 └─ on meeting end:
                      ├─ fetches full transcript
                      ├─ GPT-4o extracts summary + action items
                      └─ runs all connectors concurrently:
                           ├─ Gmail: sends follow-up email
                           ├─ Google Calendar: creates events for each action item
                           ├─ Slack: posts summary to #general
                           └─ HubSpot: updates contact/deal (if IDs provided)

Bridge (port 8000) — real-time AI voice agent inside the meeting
```

---

## Starting everything

**Windows:** double-click `start.bat`

**Mac:**
```bash
chmod +x start.sh   # only needed once after cloning
./start.sh
```

Both open all 5 services in separate terminal windows.

`WEBHOOK_BASE_URL` in `.env` is your ngrok URL — it stays the same across restarts so you don't need to change it.

---

## .env checklist

```
MEETSTREAM_API_KEY=         # MeetStream dashboard
WEBHOOK_BASE_URL=           # your ngrok URL, e.g. https://xxxx.ngrok.io
SCALEKIT_ENV_URL=           # Scalekit dashboard
SCALEKIT_CLIENT_ID=         # Scalekit dashboard
SCALEKIT_CLIENT_SECRET=     # Scalekit dashboard
OPENAI_API_KEY=             # platform.openai.com/api-keys
BACKEND_URL=http://localhost:3000
```

---

## Testing the full flow

### First-time setup (do once)

1. Fill in `.env` with all keys above
2. Run `start.bat`
3. Open `http://localhost:3002`
4. In the sidebar, click **Connect Gmail** — this opens the Scalekit OAuth page. Authorize with the Google account you want to send from.
5. *(Optional)* Connect Google Calendar the same way if you want calendar events created

### Running a test meeting

1. Run `start.bat` (if not already running)
2. Open `http://localhost:3002`
3. In the **Join a meeting** box:
   - Paste a Google Meet link
   - Enter the follow-up email recipient address
   - Click **Send bot**
4. The bot joins — watch the status badge change to **joining** then **inmeeting**
5. Talk for a bit (the transcript appears live in the dashboard)
6. End the meeting
7. After ~30 seconds the bot leaves and the webhook fires. Watch the **Webhook Server :3001** terminal for:
   ```
   [EXTRACTION] Done — N action items...
   [GMAIL] Follow-up email sent to ...
   [CONNECTOR:google_calendar] Created event '...'
   ```
8. Back in the dashboard, click **Generate summary** to get a GPT-4o recap
9. To test the late-joiner brief: type a name and click **Generate brief** while the transcript has content

> Google Meet works out of the box. Zoom requires Zoom OAuth in the MeetStream dashboard.

---

## Connector status

| Connector | Status | Needs |
|---|---|---|
| Gmail follow-up email | Ready | Gmail connected via dashboard + recipient email entered |
| Google Calendar events | Ready | Google Calendar connected via Scalekit |
| Slack summary | Ready (unverified) | Slack connected via Scalekit — `slack_send_message` tool name not yet confirmed |
| HubSpot | Ready | Needs HubSpot connected via Scalekit. Creates a deal using company/project name from the transcript. Contact update requires a `hubspot_contact_id` (skipped if not present). |

---

## What works

| Feature | Status |
|---|---|
| Send bot from dashboard | Working |
| Bot status updates (joining / inmeeting / stopped) | Working |
| Live transcript in dashboard | Working |
| Post-call extraction (GPT-4o) | Working — needs `OPENAI_API_KEY` |
| Generate summary (GPT-4o) | Working — needs `OPENAI_API_KEY` |
| Late joiner brief (GPT-4o) | Working — needs `OPENAI_API_KEY` |
| Connect Gmail from dashboard | Working |
| Gmail follow-up email | Working — needs Gmail connected + recipient email |
| Google Calendar event creation | Working — needs Google Calendar connected |
| Real-time in-meeting AI agent (bridge) | Working — needs `OPENAI_API_KEY` |

---

## Adding a connector

Drop a file in `connectors/` with an `async def run(extraction: dict)` function. The dispatcher picks it up automatically — no other changes needed.

```python
# connectors/my_connector.py
async def run(extraction: dict) -> None:
    summary = extraction.get("summary", "")
    action_items = extraction.get("action_items", [])
    ...
```

The `extraction` dict shape:
```python
{
    "summary": "str",
    "action_items": [{"title": "str", "owner": "str", "due": "str"}],
    "recipient_email": "str",
    "recipient_name": "str",
    "participants": ["str"]
}
```

---

## File map

```
start.bat                  ← Windows: double-click to start all 5 services
start.sh                   ← Mac: ./start.sh
server.py                  ← webhook server (port 3001)
extraction.py              ← GPT-4o post-call extraction
transcript.py              ← fetches transcript from MeetStream after meeting ends
send_bot.py                ← CLI fallback: uv run python send_bot.py "<link>"
auth.py                    ← Scalekit client + OAuth helpers
dispatcher.py              ← auto-discovers and runs all connectors concurrently
connectors/
  gmail_followup.py        ← sends follow-up email via Gmail API
  google_calendar.py       ← creates calendar events via Scalekit
  slack.py                 ← posts summary to Slack via Scalekit
  hubspot.py               ← updates HubSpot contact/deal via Scalekit
backend/
  main.py                  ← dashboard backend (port 3000), WebSocket, GPT-4o, join/auth endpoints
dashboard/                 ← Next.js frontend (port 3002)
app/
  server.py                ← real-time bridge to OpenAI Realtime API (port 8000)
sample_transcript.json     ← real transcript for testing extraction offline
.env.example               ← copy to .env and fill in
```

---

## Notes

- The `bot_id → transcript_id` mapping is in-memory. If the webhook server restarts between bot creation and meeting end, the mapping is lost and the transcript won't be fetched.
- `STUB_USER_ID = "hackathon-user"` is hardcoded in all connectors — all users share one Scalekit connected account.
- ngrok free tier changes URL on restart — keep it running and update `WEBHOOK_BASE_URL` if it does change.
