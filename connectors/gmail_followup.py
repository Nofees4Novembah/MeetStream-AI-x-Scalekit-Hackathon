"""
Gmail follow-up connector — sends a post-meeting summary email via Scalekit.

Scalekit proxies the Gmail API call using the user's connected account,
so we never handle OAuth tokens directly.
"""

import auth

STUB_USER_ID = "hackathon-user"


def _build_body(extraction: dict) -> str:
    recipient_name = extraction.get("recipient_name", "there")
    summary = extraction.get("summary", "No summary available.")
    action_items = extraction.get("action_items", [])

    lines = [
        f"Hi {recipient_name},",
        "",
        "Thanks for the meeting! Here's a quick recap:",
        "",
        summary,
    ]

    if action_items:
        lines += ["", "Action items:"]
        for item in action_items:
            title = item.get("title", "")
            owner = item.get("owner", "")
            due = item.get("due", "")
            lines.append(f"  - {title} (Owner: {owner}, Due: {due})")

    lines += ["", "Best,", "MeetStream Notetaker"]
    return "\n".join(lines)


async def run(extraction: dict) -> None:
    print("[GMAIL] Running follow-up connector")

    recipient = extraction.get("recipient_email", "")
    if not recipient:
        print("[GMAIL] No recipient_email in extraction, skipping")
        return

    auth_status = auth.ensure_authorized(STUB_USER_ID, connection_name="gmail")
    if not auth_status["authorized"]:
        print(f"[GMAIL] Not authorized — auth link: {auth_status['auth_link']}")
        return

    subject = "Follow-up: Meeting Summary & Action Items"
    body = _build_body(extraction)

    try:
        # Scalekit's execute_tool proxies the call using the user's connected Gmail account.
        # tool_name="gmail_send_email" sends via Gmail API — no token handling needed.
        actions = auth.get_actions()
        result = actions.execute_tool(
            tool_name="gmail_send_email",
            identifier=STUB_USER_ID,
            tool_input={
                "to": recipient,
                "subject": subject,
                "body": body,
            },
        )
        print(f"[GMAIL] Follow-up email sent to {recipient} (execution_id={result.execution_id})")
    except Exception as e:
        print(f"[GMAIL] Failed to send email: {e}")
