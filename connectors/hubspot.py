"""
HubSpot connector — creates deals and updates contacts from meeting data.

Scalekit proxies the HubSpot API call using the user's connected account.
"""

import auth

STUB_USER_ID = "hackathon-user"


async def run(extraction: dict) -> None:
    print("[HUBSPOT] Running connector")

    auth_status = auth.ensure_authorized(STUB_USER_ID, connection_name="hubspot")
    if not auth_status["authorized"]:
        print(f"[HUBSPOT] Not authorized — auth link: {auth_status['auth_link']}")
        return

    actions = auth.get_actions()

    await _update_contact(actions, extraction)
    await _create_deal(actions, extraction)


async def _update_contact(actions, extraction: dict) -> None:
    contact_id = extraction.get("hubspot_contact_id")
    if not contact_id:
        print("[HUBSPOT] No contact_id in extraction, skipping contact update")
        return

    summary = extraction.get("summary", "")

    try:
        result = actions.execute_tool(
            tool_name="hubspot_contact_update",
            identifier=STUB_USER_ID,
            tool_input={
                "contact_id": contact_id,
                "props": {
                    "hs_lead_status": "IN_PROGRESS",
                    "website": summary[:100] if summary else "",
                },
            },
        )
        print(f"[HUBSPOT] Contact {contact_id} updated (execution_id={result.execution_id})")
    except Exception as e:
        print(f"[HUBSPOT] Failed to update contact: {e}")


async def _create_deal(actions, extraction: dict) -> None:
    deal_name = extraction.get("deal_name")
    if not deal_name:
        print("[HUBSPOT] No deal_name in extraction, skipping deal creation")
        return

    amount = extraction.get("deal_amount", 0)
    stage = extraction.get("deal_stage", "appointmentscheduled")
    summary = extraction.get("summary", "")

    try:
        result = actions.execute_tool(
            tool_name="hubspot_deal_create",
            identifier=STUB_USER_ID,
            tool_input={
                "dealname": deal_name,
                "amount": amount,
                "dealstage": stage,
                "description": summary,
            },
        )
        print(f"[HUBSPOT] Deal '{deal_name}' created (execution_id={result.execution_id})")
    except Exception as e:
        print(f"[HUBSPOT] Failed to create deal: {e}")