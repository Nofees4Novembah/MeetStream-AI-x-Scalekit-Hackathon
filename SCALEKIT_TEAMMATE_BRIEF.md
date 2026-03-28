# Scalekit Teammate Brief

Hi Claude! I'm Person 3 on a hackathon team. My job is to build the Scalekit connector(s) that fire after a meeting transcript has been processed. Please read this file and tell me exactly what I need to implement.

---

## What the project does (big picture)

1. A MeetStream bot joins a meeting and records it
2. When the meeting ends, our server fetches the full transcript
3. Person 2 runs LLM extraction on the transcript → structured output (action items, owners, etc.)
4. **My job (Person 3):** take that structured output and do things with it via Scalekit — create calendar events, send emails, whatever makes sense
5. Person 4 builds a Streamlit dashboard on top

---

## What's already built for me

### `auth.py` — Scalekit client + OAuth helpers (already written, don't touch)

```python
connect_user(user_id)      # get_or_create connected account for googlecalendar
get_auth_link(user_id)     # returns OAuth link if user needs to authorize
is_authorized(user_id)     # returns True if connection status == "ACTIVE"
ensure_authorized(user_id) # returns {"authorized": True} or {"authorized": False, "auth_link": "..."}
```

Uses `scalekit-sdk-python` (already installed). Reads `SCALEKIT_CLIENT_ID`, `SCALEKIT_CLIENT_SECRET`, `SCALEKIT_ENV_URL` from `.env`.

### `connectors/google_calendar.py` — stub connector (this is the main file I need to fill in)

```python
async def run(extraction: dict) -> None:
    # checks auth via auth.ensure_authorized()
    # pulls action_items from extraction dict
    # TODO: actually call Scalekit to create calendar events
```

### `dispatcher.py` — auto-discovers and runs all connector modules concurrently

I don't need to touch this. It scans the `connectors/` folder and calls `run(extraction)` on every module it finds.

---

## How to add a connector

Drop a file in `connectors/` with an async `run(extraction: dict)` function. That's it — the dispatcher picks it up automatically. Example:

```python
# connectors/my_connector.py
async def run(extraction: dict) -> None:
    ...
```

---

## The extraction schema (not finalised yet)

Person 2 hasn't locked this down. For now assume something like:

```python
{
    "action_items": [
        {"title": "Follow up with client", "owner": "Quinn", "due": "2026-03-30"}
    ],
    "summary": "Brief meeting summary...",
    "participants": ["Quinn", "Nafis"]
}
```

Use `extraction.get("action_items", [])` with safe fallbacks so nothing breaks when the real schema lands.

---

## Sample transcript (for context on what Person 2 is working with)

The transcript is a list of speaker-turn dicts:

```python
[
    {
        "speaker": "Quinn",
        "transcript": "We need to follow up with the client by Friday.",
        "start_time": 0.0,
        "end_time": 5.2
    },
    ...
]
```

A real example is in `sample_transcript.json` in the project root.

---

## My actual tasks

1. **Fill in `connectors/google_calendar.py`** — replace the TODO with real Scalekit API calls to create a Google Calendar event for each action item. The auth check is already there.

2. **Figure out the right Scalekit API call** — `auth.actions` is a proxy to `ScalekitClient.actions`. I need to find what method creates a calendar event. The Scalekit SDK is `scalekit-sdk-python==2.4.13`.

3. **Handle the stub user ID** — `STUB_USER_ID = "hackathon-user"` is hardcoded for now. Eventually Person 4's dashboard will pass a real user identity. For now, hardcoded is fine.

4. **Optionally add more connectors** — if there's time, additional connectors (e.g. email summary) just need a new file in `connectors/`.

---

## Environment

- Python 3.13, managed with `uv`
- Run the server: `uv run python server.py` (port 3001)
- `.env` has `SCALEKIT_ENV_URL`, `SCALEKIT_CLIENT_ID`, `SCALEKIT_CLIENT_SECRET` already filled in
- Scalekit environment: `https://hackathon328.scalekit.dev`

---

## Questions to ask Claude

- What Scalekit SDK method do I use to create a Google Calendar event via the actions API?
- What does the full method signature look like?
- Should I be doing anything with the OAuth callback/redirect in a FastAPI context, or is the `ensure_authorized` helper enough?
- What's the right way to handle the case where the user hasn't authorized yet during a demo?
