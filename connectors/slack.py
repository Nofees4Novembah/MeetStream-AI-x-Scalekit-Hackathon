"""
Slack connector — sends a post-meeting summary message to a Slack channel.

Scalekit proxies the Slack API call using the user's connected account.
"""

import auth

STUB_USER_ID = "hackathon-user"


async def run(extraction: dict) -> None:
    print("[SLACK] Running connector")

    auth_status = auth.ensure_authorized(STUB_USER_ID, connection_name="slack")
    if not auth_status["authorized"]:
        print(f"[SLACK] Not authorized — auth link: {auth_status['auth_link']}")
        return

    summary = extraction.get("summary", "No summary available.")
    action_items = extraction.get("action_items", [])
    participants = extraction.get("participants", [])

    # Build the message
    lines = [
        "*Meeting Summary*",
        "",
        summary,
    ]

    if action_items:
        lines += ["", "*Action Items:*"]
        for item in action_items:
            title = item.get("title", "")
            owner = item.get("owner", "")
            due = item.get("due", "")
            lines.append(f"  • {title} (Owner: {owner}, Due: {due})")

    if participants:
        lines += ["", f"*Participants:* {', '.join(participants)}"]

    message = "\n".join(lines)

    # Channel to post to — can be overridden by extraction if Person 2 provides it
    channel = extraction.get("slack_channel", "#general")

    try:
        actions = auth.get_actions()
        result = actions.execute_tool(
            tool_name="slack_send_message",
            identifier=STUB_USER_ID,
            tool_input={
                "channel": channel,
                "text": message,
            },
        )
        print(f"[SLACK] Message sent to {channel} (execution_id={result.execution_id})")
    except Exception as e:
        print(f"[SLACK] Failed to send message: {e}")