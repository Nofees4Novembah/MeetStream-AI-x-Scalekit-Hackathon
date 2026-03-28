"""
Standalone test for the Gmail follow-up connector.
Run with: uv run python test_gmail.py

Fill in recipient_email before running.
"""

import asyncio
import auth
from connectors.gmail_followup import run, STUB_USER_ID

TEST_EXTRACTION = {
    "recipient_email": "YOUR_EMAIL_HERE",  # fill in before running
    "recipient_name": "Test Recipient",
    "summary": "We discussed the Q2 roadmap and assigned action items.",
    "action_items": [
        {"title": "Draft proposal for client", "owner": "Quinn", "due": "2026-03-30"},
        {"title": "Set up staging environment", "owner": "Nafis", "due": "2026-03-31"},
    ],
    "participants": ["Quinn", "Nafis"],
}


async def main() -> None:
    print(f"[TEST] Checking Gmail auth for user '{STUB_USER_ID}'...")

    if not auth.is_authorized(STUB_USER_ID, connection_name="gmail"):
        link = auth.get_auth_link(STUB_USER_ID, connection_name="gmail")
        print(f"[TEST] Not authorized. Open this link to connect Gmail:\n\n  {link}\n")
        print("[TEST] After authorizing, re-run this script.")
        return

    print("[TEST] Gmail authorized. Sending test email...")
    await run(TEST_EXTRACTION)


if __name__ == "__main__":
    asyncio.run(main())
