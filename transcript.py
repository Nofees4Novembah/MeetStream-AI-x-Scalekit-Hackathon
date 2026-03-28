import json
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

MEETSTREAM_API_KEY = os.getenv("MEETSTREAM_API_KEY")
BASE_URL = "https://api.meetstream.ai/api/v1"


async def fetch_transcript(transcript_id: str) -> dict:
    headers = {"Authorization": f"Token {MEETSTREAM_API_KEY}"}
    url = f"{BASE_URL}/transcript/{transcript_id}/get_transcript"

    async with httpx.AsyncClient() as client:
        # Fetch structured transcript
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"[TRANSCRIPT] Error fetching transcript: {resp.status_code} {resp.text}")
            return {}
        structured = resp.json()
        print(f"[TRANSCRIPT] Structured transcript fetched ({len(str(structured))} chars)")
        with open("sample_transcript.json", "w") as f:
            json.dump(structured, f, indent=2)
        print("[TRANSCRIPT] Saved to sample_transcript.json")

        # Fetch raw transcript — includes more granular word-level timing data
        raw_resp = await client.get(url, headers=headers, params={"raw": "True"})
        if raw_resp.status_code != 200:
            print(f"[TRANSCRIPT] Error fetching raw transcript: {raw_resp.status_code} {raw_resp.text}")
        else:
            raw = raw_resp.json()
            print(f"[TRANSCRIPT] Raw transcript fetched ({len(str(raw))} chars)")

    return structured
