import json
import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

MEETSTREAM_API_KEY = os.getenv("MEETSTREAM_API_KEY")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL")


def main() -> None:
    if len(sys.argv) < 2:
        print("[BOT] Usage: python send_bot.py \"https://zoom.us/j/123456\"")
        sys.exit(1)

    meeting_link = sys.argv[1]
    print(f"[BOT] Sending bot to: {meeting_link}")

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

    headers = {"Authorization": f"Token {MEETSTREAM_API_KEY}"}
    resp = httpx.post(
        "https://api.meetstream.ai/api/v1/bots/create_bot",
        json=payload,
        headers=headers,
    )

    print(f"[BOT] Response status: {resp.status_code}")
    data = resp.json()
    print(json.dumps(data, indent=2))

    bot_id = data.get("bot_id") or data.get("id")
    transcript_id = data.get("transcript_id")
    print(f"[BOT] bot_id={bot_id}  transcript_id={transcript_id}")

    # Register the bot_id -> transcript_id mapping with our server so that
    # when transcription.processed arrives (which only includes bot_id), we
    # can look up the transcript_id to fetch the right transcript.
    reg = httpx.post(
        f"{WEBHOOK_BASE_URL}/register_bot",
        json={"bot_id": bot_id, "transcript_id": transcript_id},
    )
    print(f"[BOT] Registered mapping with server: {reg.status_code} {reg.text}")


if __name__ == "__main__":
    main()
