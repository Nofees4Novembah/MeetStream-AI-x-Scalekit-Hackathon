"""
Standalone test for the HubSpot connector.
Run with: uv run python test_hubspot.py

Fill in hubspot_contact_id before running.
You can find a contact ID in your HubSpot dashboard under Contacts.
"""

import asyncio
import auth
from connectors.hubspot import run, STUB_USER_ID

TEST_EXTRACTION = {
    "hubspot_contact_id": "462551339707",  # fill in before running
    "deal_name": "Q2 Follow-up Deal",
    "deal_amount": 5000,
    "deal_stage": "appointmentscheduled",
    "summary": "We discussed the Q2 roadmap and assigned action items.",
    "action_items": [
        {"title": "Follow up with client", "owner": "Quinn", "due": "2026-03-30"},
        {"title": "Set up staging environment", "owner": "Nafis", "due": "2026-03-31"},
    ],
    "participants": ["Quinn", "Nafis"],
}


async def main() -> None:
    print(f"[TEST] Checking HubSpot auth for user '{STUB_USER_ID}'...")

    if not auth.is_authorized(STUB_USER_ID, connection_name="hubspot"):
        link = auth.get_auth_link(STUB_USER_ID, connection_name="hubspot")
        print(f"[TEST] Not authorized. Open this link to connect HubSpot:\n\n  {link}\n")
        print("[TEST] After authorizing, re-run this script.")
        return

    print("[TEST] HubSpot authorized. Running test...")
    await run(TEST_EXTRACTION)


if __name__ == "__main__":
    asyncio.run(main())