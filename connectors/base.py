from typing import Protocol, runtime_checkable


@runtime_checkable
class Connector(Protocol):
    """
    Interface every connector must implement.

    Each connector receives the structured extraction output from Person 2
    and does whatever it needs to do (create calendar events, send emails, etc.).

    To add a new connector:
      1. Create a new file in connectors/ (e.g. connectors/slack.py)
      2. Define an async run(extraction: dict) function
      3. That's it — dispatcher.py picks it up automatically
    """

    async def run(self, extraction: dict) -> None:
        ...
