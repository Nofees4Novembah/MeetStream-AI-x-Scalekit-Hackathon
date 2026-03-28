"""
Standalone test for the Slack connector.
Run with: uv run python test_slack.py
"""

import asyncio
import auth
from connectors.slack import run, STUB_USER_ID

TEST_EXTRACTION = {
    "summary": "We discussed the Q2 roadmap and assigned action items.",
    "action_items": [
        {"title": "Follow up with client", "owner": "Quinn", "due": "2026-03-30"},
        {"title": "Set up staging environment", "owner": "Nafis", "due": "2026-03-31"},
    ],
    "participants": ["Quinn", "Nafis"],
    "slack_channel": "#general",
}


async def main() -> None:
    print(f"[TEST] Checking Slack auth for user '{STUB_USER_ID}'...")

    if not auth.is_authorized(STUB_USER_ID, connection_name="slack"):
        link = auth.get_auth_link(STUB_USER_ID, connection_name="slack")
        print(f"[TEST] Not authorized. Open this link to connect Slack:\n\n  {link}\n")
        print("[TEST] After authorizing, re-run this script.")
        return

    print("[TEST] Slack authorized. Sending test message...")
    await run(TEST_EXTRACTION)


if __name__ == "__main__":
    asyncio.run(main())