"""
Lists all tools available in your Scalekit environment for hackathon-user.
Run with: uv run python debug_tools.py
"""

import json
import auth
from scalekit.v1.tools.tools_pb2 import ScopedToolFilter

STUB_USER_ID = "hackathon-user"

def print_scoped_tools(actions, connection_name: str) -> None:
    print(f"\n=== {connection_name} tools for '{STUB_USER_ID}' ===")
    try:
        resp, _ = actions.tools.list_scoped_tools(
            identifier=STUB_USER_ID,
            filter=ScopedToolFilter(connection_names=[connection_name]),
        )
        if resp.tool_names:
            print(f"  tool_names: {list(resp.tool_names)}")
        for scoped_tool in resp.tools:
            t = scoped_tool.tool
            print(f"\n  [{t.id}] provider={t.provider}")
            # Print input schema if available
            try:
                schema = json.loads(t.input_schema) if hasattr(t, "input_schema") and t.input_schema else None
                if schema:
                    props = schema.get("properties", {})
                    required = schema.get("required", [])
                    for field, meta in props.items():
                        req = " (required)" if field in required else ""
                        desc = meta.get("description", "")
                        print(f"    - {field}{req}: {desc}")
            except Exception:
                pass
    except Exception as e:
        print(f"  failed: {e}")

def main() -> None:
    actions = auth.get_actions()

    print("=== All tools ===")
    try:
        resp, _ = actions.tools.list_tools()
        tool_names = list(resp.tool_names)
        tools = list(resp.tools)
        for i, tool in enumerate(tools):
            name = tool_names[i] if i < len(tool_names) else "(no name)"
            print(f"  {tool.id} | {tool.provider} | {name}")
    except Exception as e:
        print(f"  list_tools() failed: {e}")

    for conn in ["gmail", "googlecalendar", "slack", "hubspot"]:
        print_scoped_tools(actions, conn)

if __name__ == "__main__":
    main()
