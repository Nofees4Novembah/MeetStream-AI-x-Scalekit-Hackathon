"""
Lists all tools available in your Scalekit environment for hackathon-user.
Run with: uv run python debug_tools.py
"""

import auth
from scalekit.v1.tools.tools_pb2 import ScopedToolFilter

STUB_USER_ID = "hackathon-user"

def main() -> None:
    actions = auth.get_actions()

    print("=== All tools: id | provider | tool_name ===")
    try:
        resp, _ = actions.tools.list_tools()
        tool_names = list(resp.tool_names)
        tools = list(resp.tools)
        for i, tool in enumerate(tools):
            name = tool_names[i] if i < len(tool_names) else "(no name)"
            print(f"  {tool.id} | {tool.provider} | {name}")
    except Exception as e:
        print(f"  list_tools() failed: {e}")

    print(f"\n=== Gmail-scoped tools for '{STUB_USER_ID}' ===")
    try:
        resp, _ = actions.tools.list_scoped_tools(
            identifier=STUB_USER_ID,
            filter=ScopedToolFilter(connection_names=["gmail"]),
        )
        for scoped_tool in resp.tools:
            print(f"  {scoped_tool.tool.id} | {scoped_tool.tool.provider}")
        # Also print the tool_names summary field if present
        if resp.tool_names:
            print(f"  tool_names: {list(resp.tool_names)}")
    except Exception as e:
        print(f"  list_scoped_tools() failed: {e}")

if __name__ == "__main__":
    main()
