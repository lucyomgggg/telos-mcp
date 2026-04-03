"""Telos MCP server: exposes Telos Core memory tools over MCP."""

from __future__ import annotations

import argparse
import json
import os

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

from client import TelosClient
from config import load_settings

mcp = FastMCP("Telos")


@mcp.custom_route("/", methods=["GET"])
async def _railway_health(request: Request) -> JSONResponse:
    """Liveness probe for Railway (GET /). MCP HTTP endpoint remains at /mcp."""
    return JSONResponse({"status": "ok"})

_TELOS_WRITE_DESC = (
    "Write a memory to Telos shared memory pool. Use this to store insights, "
    "observations, results, or any information worth preserving for future agents."
)

_TELOS_SEARCH_DESC = (
    "Search Telos shared memory pool using semantic similarity. Returns the most "
    "relevant memories across all Monads."
)

_TELOS_STATUS_DESC = (
    "Check if Telos Core is reachable and return connection info."
)


def _tool_error(prefix: str, exc: BaseException) -> str:
    return f"{prefix}: {exc}"


@mcp.tool(name="telos_write", description=_TELOS_WRITE_DESC)
async def telos_write(
    content: str,
    monad_id: str | None = None,
    parent_ids: list[str] | None = None,
) -> str:
    try:
        settings = load_settings()
    except ValueError as e:
        return _tool_error("Configuration error", e)

    mid = monad_id or settings.default_monad_id
    client = TelosClient(settings.telos_base_url)
    try:
        result = await client.write(mid, content, parent_ids)
    except Exception as e:
        return _tool_error("telos_write failed", e)
    return f"Written successfully. UUID: {result['uuid']}"


@mcp.tool(name="telos_search", description=_TELOS_SEARCH_DESC)
async def telos_search(
    query: str,
    monad_id: str | None = None,
    top_k: int | None = None,
) -> str:
    try:
        settings = load_settings()
    except ValueError as e:
        return _tool_error("Configuration error", e)

    k = top_k if top_k is not None else settings.default_top_k
    mid = monad_id or settings.default_monad_id
    client = TelosClient(settings.telos_base_url)
    try:
        hits = await client.search(mid, query, k)
    except Exception as e:
        return _tool_error("telos_search failed", e)

    if not hits:
        return "No results found."
    return json.dumps(hits, ensure_ascii=False)


@mcp.tool(name="telos_status", description=_TELOS_STATUS_DESC)
async def telos_status() -> str:
    try:
        settings = load_settings()
    except ValueError as e:
        return _tool_error("Configuration error", e)

    client = TelosClient(settings.telos_base_url)
    try:
        return await client.probe_reachable()
    except Exception as e:
        return _tool_error("telos_status failed", e)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Telos MCP server")
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "sse", "streamable-http"],
        help="MCP transport (default: stdio for local Claude)",
    )
    default_port = int(os.environ.get("PORT", "8000"))
    parser.add_argument(
        "--port",
        type=int,
        default=default_port,
        help="Listen port for HTTP transports (default: $PORT or 8000)",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Bind address for HTTP transports (default: 0.0.0.0 for streamable-http, 127.0.0.1 for sse)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.transport == "sse":
        host = args.host
        if host is None:
            host = "127.0.0.1"
        mcp.settings = mcp.settings.model_copy(update={"host": host, "port": args.port})
    elif args.transport == "streamable-http":
        # FastMCP.run() は host/port/allowed_hosts を受け取らないため、設定を mcp.settings に載せる。
        # Host にポート付きの場合は :* パターンで許可（localhost / Railway）。
        _hosts = [
            "telos-mcp-production.up.railway.app",
            "telos-mcp-production.up.railway.app:*",
            "localhost",
            "localhost:*",
            "127.0.0.1",
            "127.0.0.1:*",
        ]
        _origins = [
            "https://telos-mcp-production.up.railway.app",
            "https://telos-mcp-production.up.railway.app:*",
            "http://localhost:*",
            "http://127.0.0.1:*",
            "http://localhost",
            "http://127.0.0.1",
        ]
        mcp.settings = mcp.settings.model_copy(
            update={
                "host": "0.0.0.0",
                "port": int(os.environ.get("PORT", 8000)),
                "transport_security": TransportSecuritySettings(
                    enable_dns_rebinding_protection=True,
                    allowed_hosts=_hosts,
                    allowed_origins=_origins,
                ),
            }
        )

    if args.transport == "stdio":
        print(
            "Telos MCP server running — transport=stdio "
            "(waiting for MCP client on stdin/stdout).",
            flush=True,
        )
    elif args.transport == "streamable-http":
        s = mcp.settings
        print(
            f"Telos MCP server running — transport=streamable-http "
            f"http://{s.host}:{s.port}{s.streamable_http_path}",
            flush=True,
        )
    elif args.transport == "sse":
        s = mcp.settings
        print(
            f"Telos MCP server running — transport=sse "
            f"http://{s.host}:{s.port}{s.sse_path}",
            flush=True,
        )

    if args.transport == "streamable-http":
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport=args.transport)
