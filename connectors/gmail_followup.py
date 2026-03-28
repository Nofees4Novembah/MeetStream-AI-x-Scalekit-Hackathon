"""
Gmail follow-up connector — sends a post-meeting summary email.

Scalekit manages the OAuth connection. We fetch the access token from the
connected account and call the Gmail API directly, since no gmail_send_email
execute_tool exists in this Scalekit environment.
"""

import base64
from email.mime.text import MIMEText

import httpx

import auth

STUB_USER_ID = "hackathon-user"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


def _get_access_token() -> str | None:
    account = auth.connect_user(STUB_USER_ID, connection_name="gmail")
    try:
        return account.authorization_details["oauth_token"]["access_token"]
    except (KeyError, TypeError):
        return None


def _build_mime(recipient: str, subject: str, body: str) -> str:
    msg = MIMEText(body)
    msg["to"] = recipient
    msg["subject"] = subject
    # Gmail API requires base64url encoding (no padding)
    return base64.urlsafe_b64encode(msg.as_bytes()).decode().rstrip("=")


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

    access_token = _get_access_token()
    if not access_token:
        print("[GMAIL] Could not retrieve access token from connected account")
        return

    subject = "Follow-up: Meeting Summary & Action Items"
    raw = _build_mime(recipient, subject, _build_body(extraction))

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GMAIL_SEND_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                json={"raw": raw},
            )

        if resp.status_code == 200:
            print(f"[GMAIL] Follow-up email sent to {recipient}")
        else:
            print(f"[GMAIL] Gmail API error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"[GMAIL] Failed to send email: {e}")
