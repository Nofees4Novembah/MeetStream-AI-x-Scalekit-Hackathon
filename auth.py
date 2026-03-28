import os
from dotenv import load_dotenv
from scalekit import ScalekitClient # type: ignore
from typing import Any

load_dotenv()

scalekit_client = ScalekitClient(
    client_id=os.getenv("SCALEKIT_CLIENT_ID"),
    client_secret=os.getenv("SCALEKIT_CLIENT_SECRET"),
    env_url=os.getenv("SCALEKIT_ENV_URL"),
)

actions = scalekit_client.actions

def connect_user(user_id: str) -> Any:
    response = actions.get_or_create_connected_account(
        connection_name="googlecalendar",
        identifier=user_id
    )
    return response.connected_account

def get_auth_link(user_id: str) -> Any:
    link_response = actions.get_authorization_link(
        connection_name="googlecalendar",
        identifier=user_id
    )
    return link_response.link

def is_authorized(user_id: str) -> bool:
    account = connect_user(user_id)
    return bool(account.status == "ACTIVE")

def ensure_authorized(user_id: str) -> Any:
    account = connect_user(user_id)

    if account.status != "ACTIVE":
        link = get_auth_link(user_id)
        print(f"User {user_id} needs to authorize. Send them this link:")
        print(link)
        return {"authorized": False, "auth_link": link}

    return {"authorized": True}