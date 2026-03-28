"""
Google Calendar connector — creates calendar events for action items.

Depends on auth.py for Scalekit OAuth. Once Person 2 finalises the
extraction schema, replace the TODO comments with real field access.
"""

import auth

STUB_USER_ID = "hackathon-user"


async def run(extraction: dict) -> None:
    print("[CONNECTOR:google_calendar] Running")

    auth_status = auth.ensure_authorized(STUB_USER_ID)
    if not auth_status["authorized"]:
        print(f"[CONNECTOR:google_calendar] User not authorized. Auth link: {auth_status['auth_link']}")
        return

    raw_action_items = extraction.get("action_items")
    if raw_action_items is None:
        raw_action_items = extraction.get("actions")
    if raw_action_items is None:
        raw_action_items = extraction.get("tasks")
    if raw_action_items is None:
        raw_action_items = extraction.get("actionItems")

    if not isinstance(raw_action_items, list):
        raw_action_items = []

    action_items = []
    for item in raw_action_items:
        if not isinstance(item, dict):
            continue

        title = (
            item.get("title")
            or item.get("task")
            or item.get("name")
            or item.get("description")
            or ""
        )
        owner = (
            item.get("owner")
            or item.get("assignee")
            or item.get("person")
            or item.get("participant")
            or ""
        )
        due = (
            item.get("due")
            or item.get("due_date")
            or item.get("deadline")
            or item.get("date")
            or ""
        )

        if title:
            action_items.append({
                "title": title,
                "owner": owner,
                "due": due,
            })

    if not action_items:
        print("[CONNECTOR:google_calendar] No action items to schedule")
        return

    actions = auth.get_actions()

    for item in action_items:
        title = item["title"]
        owner = item["owner"]
        due = item["due"]

        event_title = f"{title}" + (f" — {owner}" if owner else "")
        from datetime import datetime, timezone, timedelta
        start_datetime = due if due else (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT09:00:00Z")

        try:
            result = actions.execute_tool(
                tool_name="googlecalendar_create_event",
                identifier=STUB_USER_ID,
                tool_input={
                    "summary": event_title,
                    "start_datetime": start_datetime,
                    "event_duration_minutes": 30,
                    "description": f"Action item from meeting.\nOwner: {owner}\nDue: {due}",
                    "timezone": "America/Los_Angeles",
                },
            )
            print(f"[CONNECTOR:google_calendar] Created event '{event_title}' (execution_id={result.execution_id})")
        except Exception as e:
            print(f"[CONNECTOR:google_calendar] Failed to create event '{event_title}': {e}")