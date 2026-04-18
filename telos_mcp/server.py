"""Telos MCP server: exposes Telos Core memory tools over MCP."""

from __future__ import annotations

import argparse
import os

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

from telos_mcp.tools import register_tools

mcp = FastMCP("Telos")
register_tools(mcp)


def _public_base_host() -> str:
    return os.environ.get("RAILWAY_PUBLIC_DOMAIN", "localhost:8000")


def _resource_url() -> str:
    return f"https://{_public_base_host()}"


@mcp.custom_route("/", methods=["GET"])
async def railway_health(request: Request) -> JSONResponse:
    """Liveness probe for Railway (GET /). MCP HTTP endpoint remains at /mcp."""
    return JSONResponse({"status": "ok"})


@mcp.custom_route("/.well-known/oauth-protected-resource", methods=["GET"])
async def oauth_protected_resource(request: Request) -> JSONResponse:
    """OAuth discovery: advertise this resource URL (no auth required for this server)."""
    return JSONResponse({"resource": _resource_url()})


@mcp.custom_route("/.well-known/oauth-authorization-server", methods=["GET"])
async def oauth_authorization_server(request: Request) -> JSONResponse:
    """Explicit 404 so clients do not treat this host as an OAuth authorization server."""
    return JSONResponse({}, status_code=404)


@mcp.custom_route("/.well-known/openid-configuration", methods=["GET"])
async def openid_configuration(request: Request) -> JSONResponse:
    """Explicit 404: no OpenID Provider at this host."""
    return JSONResponse({}, status_code=404)


def parse_args() -> argparse.Namespace:
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


def configure_transport(args: argparse.Namespace) -> None:
    base_host = _public_base_host()
    if args.transport == "sse":
        host = args.host if args.host is not None else "127.0.0.1"
        mcp.settings = mcp.settings.model_copy(update={"host": host, "port": args.port})
        return

    if args.transport != "streamable-http":
        return

    allowed_hosts = [
        base_host,
        f"{base_host}:*",
        "localhost",
        "localhost:*",
        "127.0.0.1",
        "127.0.0.1:*",
    ]
    allowed_origins = [
        f"https://{base_host}",
        f"https://{base_host}:*",
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
                allowed_hosts=allowed_hosts,
                allowed_origins=allowed_origins,
            ),
        }
    )


def announce_transport(args: argparse.Namespace) -> None:
    if args.transport == "stdio":
        print(
            "Telos MCP server running — transport=stdio "
            "(waiting for MCP client on stdin/stdout).",
            flush=True,
        )
        return

    settings = mcp.settings
    if args.transport == "streamable-http":
        print(
            f"Telos MCP server running — transport=streamable-http "
            f"http://{settings.host}:{settings.port}{settings.streamable_http_path}",
            flush=True,
        )
        return

    print(
        f"Telos MCP server running — transport=sse "
        f"http://{settings.host}:{settings.port}{settings.sse_path}",
        flush=True,
    )


def run(args: argparse.Namespace) -> None:
    if args.transport == "streamable-http":
        mcp.run(transport="streamable-http")
        return
    mcp.run(transport=args.transport)


def main() -> None:
    args = parse_args()
    configure_transport(args)
    announce_transport(args)
    run(args)
