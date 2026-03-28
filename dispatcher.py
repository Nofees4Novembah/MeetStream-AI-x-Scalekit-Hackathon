"""
Dispatcher — runs all connectors against the extraction output.

Connectors are auto-discovered from the connectors/ package: any module
that exposes an async run(extraction: dict) function is called automatically.
Nobody needs to touch this file to add a new connector.
"""

import asyncio
import importlib
import pkgutil

import connectors


def _load_connectors() -> list:
    """Return all connector modules that expose a run() function."""
    loaded = []
    for module_info in pkgutil.iter_modules(connectors.__path__):
        if module_info.name == "base":
            continue
        module = importlib.import_module(f"connectors.{module_info.name}")
        if callable(getattr(module, "run", None)):
            loaded.append(module)
    return loaded


async def dispatch(extraction: dict) -> None:
    """
    Call every connector with the extraction output.

    extraction: structured data from Person 2's LLM extraction step.
                Schema TBD — connectors should use .get() with fallbacks
                until the schema is finalised.
    """
    connector_modules = _load_connectors()

    if not connector_modules:
        print("[DISPATCHER] No connectors found")
        return

    print(f"[DISPATCHER] Running {len(connector_modules)} connector(s): "
          f"{[m.__name__ for m in connector_modules]}")

    # Run all connectors concurrently
    await asyncio.gather(*(m.run(extraction) for m in connector_modules))

    print("[DISPATCHER] All connectors finished")
