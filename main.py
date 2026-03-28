<<<<<<< HEAD
<<<<<<< HEAD
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()


if __name__ == "__main__":
    main()
=======
def main():
    print("Hello from real-time-agents!")
=======
"""CLI entry: run the MeetStream bridge (same as `uv run uvicorn app.server:app`)."""

import os


def main() -> None:
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "app.server:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=port,
        reload=os.getenv("UVICORN_RELOAD", "1") == "1",
    )
>>>>>>> f403a71 (refactor(bridge): layered MeetStream ↔ Realtime stack, MCP config, and stable TTS around tools)


if __name__ == "__main__":
    main()
>>>>>>> 0f53bb0 (Meetstream Agents)
