"""
Google Calendar connector — creates calendar events for action items.

Depends on auth.py for Scalekit OAuth. Once Person 2 finalises the
extraction schema, replace the TODO comments with real field access.
"""

import auth


# TODO: replace with real user identity once Person 4's dashboard provides it
STUB_USER_ID = "hackathon-user"


async def run(extraction: dict) -> None:
    print("[CONNECTOR:google_calendar] Running")

    auth_status = auth.ensure_authorized(STUB_USER_ID)
    if not auth_status["authorized"]:
        print(f"[CONNECTOR:google_calendar] User not authorized. Auth link: {auth_status['auth_link']}")
        return

    # TODO: swap stub for real extraction fields once Person 2 finalises schema
    # Expected something like:
    #   extraction["action_items"] -> list of {"title": str, "owner": str, "due": str}
    action_items = extraction.get("action_items", [])

    if not action_items:
        print("[CONNECTOR:google_calendar] No action items to schedule")
        return

    for item in action_items:
        print(f"[CONNECTOR:google_calendar] Would create event: {item}")
        # TODO: call Scalekit actions API to create calendar event
        # e.g. auth.actions.create_event(connection_name="googlecalendar", ...)
