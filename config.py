"""Environment-backed settings for Telos MCP."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        msg = f"{name} is required (set in environment or .env)"
        raise ValueError(msg)
    return value


def _default_monad_id() -> str:
    return os.environ.get("TELOS_DEFAULT_MONAD_ID", "mcp-monad").strip() or "mcp-monad"


def _default_top_k() -> int:
    raw = os.environ.get("TELOS_DEFAULT_TOP_K", "5").strip()
    try:
        k = int(raw)
    except ValueError as e:
        msg = f"TELOS_DEFAULT_TOP_K must be an integer, got {raw!r}"
        raise ValueError(msg) from e
    if k < 1:
        msg = "TELOS_DEFAULT_TOP_K must be >= 1"
        raise ValueError(msg)
    return k


@dataclass(frozen=True)
class Settings:
    telos_base_url: str
    default_monad_id: str
    default_top_k: int


def load_settings() -> Settings:
    base = _require_env("TELOS_BASE_URL").rstrip("/")
    return Settings(
        telos_base_url=base,
        default_monad_id=_default_monad_id(),
        default_top_k=_default_top_k(),
    )
