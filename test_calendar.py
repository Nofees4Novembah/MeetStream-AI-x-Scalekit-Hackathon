"""
Standalone test for the Google Calendar connector.
Run with: uv run python test_calendar.py
"""

import asyncio
import auth
from connectors.google_calendar import run, STUB_USER_ID

TEST_EXTRACTION = {
    "action_items": [
        {"title": "Follow up with client", "owner": "Quinn", "due": "2026-03-30T09:00:00Z"},
        {"title": "Set up staging environment", "owner": "Nafis", "due": "2026-03-31T09:00:00Z"},
    ],
    "summary": "We discussed the Q2 roadmap and assigned action items.",
    "participants": ["Quinn", "Nafis"],
}


async def main() -> None:
    print(f"[TEST] Checking Google Calendar auth for user '{STUB_USER_ID}'...")

    if not auth.is_authorized(STUB_USER_ID, connection_name="googlecalendar"):
        link = auth.get_auth_link(STUB_USER_ID, connection_name="googlecalendar")
        print(f"[TEST] Not authorized. Open this link to connect Google Calendar:\n\n  {link}\n")
        print("[TEST] After authorizing, re-run this script.")
        return

    print("[TEST] Google Calendar authorized. Creating test events...")
    await run(TEST_EXTRACTION)


if __name__ == "__main__":
    asyncio.run(main())