"""
HubSpot connector — creates deals from meeting data.

Scalekit's execute_tool serializes nested dicts to strings, which breaks
HubSpot's properties API. We fetch the OAuth token directly and call
the HubSpot API ourselves, the same pattern as gmail_followup.py.
"""

import httpx
import auth

STUB_USER_ID = "hackathon-user"
HUBSPOT_DEALS_URL = "https://api.hubapi.com/crm/v3/objects/deals"


def _get_access_token() -> str | None:
    account = auth.connect_user(STUB_USER_ID, connection_name="hubspot")
    try:
        return account.authorization_details["oauth_token"]["access_token"]
    except (KeyError, TypeError):
        return None


async def run(extraction: dict) -> None:
    print("[HUBSPOT] Running connector")

    auth_status = auth.ensure_authorized(STUB_USER_ID, connection_name="hubspot")
    if not auth_status["authorized"]:
        print(f"[HUBSPOT] Not authorized — auth link: {auth_status['auth_link']}")
        return

    deal_name = extraction.get("deal_name") or extraction.get("recipient_name")
    if not deal_name:
        print("[HUBSPOT] No deal_name in extraction, skipping")
        return

    access_token = _get_access_token()
    if not access_token:
        print("[HUBSPOT] Could not retrieve access token")
        return

    stage  = extraction.get("deal_stage") or "appointmentscheduled"
    amount = str(extraction.get("deal_amount", 0) or 0)

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                HUBSPOT_DEALS_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "properties": {
                        "dealname":   deal_name,
                        "dealstage":  stage,
                        "amount":     amount,
                    }
                },
            )

        if resp.status_code in (200, 201):
            deal_id = resp.json().get("id", "?")
            print(f"[HUBSPOT] Deal '{deal_name}' created (id={deal_id})")
        else:
            print(f"[HUBSPOT] HubSpot API error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"[HUBSPOT] Failed to create deal: {e}")
