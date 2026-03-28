import os
from dotenv import load_dotenv
from scalekit import ScalekitClient
from typing import Any


_scalekit_client = None

def get_scalekit_client() -> ScalekitClient:
    """
    Lazily create and return a configured ScalekitClient.

    Raises:
        RuntimeError: if required environment variables are missing.
    """
    global _scalekit_client
    if _scalekit_client is not None:
        return _scalekit_client

    client_id = os.getenv("SCALEKIT_CLIENT_ID")
    client_secret = os.getenv("SCALEKIT_CLIENT_SECRET")
    env_url = os.getenv("SCALEKIT_ENV_URL")

    missing = [
        name
        for name, value in [
            ("SCALEKIT_CLIENT_ID", client_id),
            ("SCALEKIT_CLIENT_SECRET", client_secret),
            ("SCALEKIT_ENV_URL", env_url),
        ]
        if not value
    ]
    if missing:
        raise RuntimeError(
            f"Missing required Scalekit configuration environment variables: {', '.join(missing)}"
        )

    _scalekit_client = ScalekitClient(
        client_id=client_id,
        client_secret=client_secret,
        env_url=env_url,
    )
    return _scalekit_client

class _ActionsProxy:
    """
    Proxy object exposing the `actions` of the lazily created ScalekitClient.
    """

    def __getattr__(self, name: str) -> Any:
        return getattr(get_scalekit_client().actions, name)


actions = _ActionsProxy()
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
    return account.status == "ACTIVE"

def ensure_authorized(user_id: str) -> Any:
    account = connect_user(user_id)

    if account.status != "ACTIVE":
        link = get_auth_link(user_id)
        print(f"User {user_id} needs to authorize. Send them this link:")
        print(link)
        return {"authorized": False, "auth_link": link}

    return {"authorized": True}