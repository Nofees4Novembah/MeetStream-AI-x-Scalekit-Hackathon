# MeetStream AI x Scalekit Hackathon

Post-call webhook server that receives MeetStream bot lifecycle events and fetches transcripts after meetings end.

## Setup

1. Copy `.env.example` to `.env` and fill in `MEETSTREAM_API_KEY`
2. Start the server:
   ```
   uv run python server.py
   ```
3. In another terminal, start ngrok:
   ```
   ngrok http 3000
   ```
4. Copy the ngrok HTTPS URL into `.env` as `WEBHOOK_BASE_URL`
5. Restart the server
6. Send a bot to a meeting:
   ```
   uv run python send_bot.py "https://zoom.us/j/your-meeting"
   ```
7. Watch the console for webhook events and transcript output

## Files

- `server.py` — FastAPI webhook server (port 3000)
- `transcript.py` — async transcript fetcher
- `send_bot.py` — CLI script to dispatch a bot to a meeting
