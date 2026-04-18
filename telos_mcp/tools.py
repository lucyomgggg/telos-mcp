from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from telos_mcp.client import TelosClient
from telos_mcp.settings import load_settings

TELOS_WRITE_DESC = (
    "Write a memory to Telos shared memory pool. Use this to store insights, "
    "observations, results, or any information worth preserving for future agents."
)

TELOS_SEARCH_DESC = (
    "Search Telos shared memory pool using semantic similarity. Returns the most "
    "relevant memories across all Monads."
)

TELOS_STATUS_DESC = (
    "Check if Telos Core is reachable and return connection info."
)


def _tool_error(prefix: str, exc: BaseException) -> str:
    return f"{prefix}: {exc}"


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool(name="telos_write", description=TELOS_WRITE_DESC)
    async def telos_write(
        content: str,
        monad_id: str | None = None,
        parent_ids: list[str] | None = None,
        kind: str | None = None,
        scope_kind: str | None = None,
        scope_id: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        try:
            settings = load_settings()
        except ValueError as exc:
            return _tool_error("Configuration error", exc)

        resolved_monad_id = monad_id or settings.default_monad_id
        client = TelosClient(settings.telos_base_url)
        try:
            result = await client.write(
                resolved_monad_id,
                content,
                parent_ids,
                kind=kind,
                scope_kind=scope_kind,
                scope_id=scope_id,
                metadata=metadata,
            )
        except Exception as exc:
            return _tool_error("telos_write failed", exc)
        return f"Written successfully. UUID: {result['uuid']}"

    @mcp.tool(name="telos_search", description=TELOS_SEARCH_DESC)
    async def telos_search(
        query: str,
        monad_id: str | None = None,
        limit: int | None = None,
        top_k: int | None = None,
        kind: str | None = None,
        scope_kind: str | None = None,
        scope_id: str | None = None,
    ) -> str:
        try:
            settings = load_settings()
        except ValueError as exc:
            return _tool_error("Configuration error", exc)

        resolved_limit = limit if limit is not None else top_k
        if resolved_limit is None:
            resolved_limit = settings.default_top_k
        resolved_monad_id = monad_id or settings.default_monad_id
        client = TelosClient(settings.telos_base_url)
        try:
            hits = await client.search(
                resolved_monad_id,
                query,
                resolved_limit,
                kind=kind,
                scope_kind=scope_kind,
                scope_id=scope_id,
            )
        except Exception as exc:
            return _tool_error("telos_search failed", exc)

        if not hits:
            return "No results found."
        return json.dumps(hits, ensure_ascii=False)

    @mcp.tool(name="telos_status", description=TELOS_STATUS_DESC)
    async def telos_status() -> str:
        try:
            settings = load_settings()
        except ValueError as exc:
            return _tool_error("Configuration error", exc)

        client = TelosClient(settings.telos_base_url)
        try:
            return await client.probe_reachable()
        except Exception as exc:
            return _tool_error("telos_status failed", exc)
