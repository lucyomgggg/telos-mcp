"""Async HTTP client for Telos Core REST API."""

from __future__ import annotations

from typing import Any

import httpx


def _error_detail(response: httpx.Response) -> str:
    try:
        body: Any = response.json()
        if isinstance(body, dict) and "detail" in body:
            return str(body["detail"])
        return str(body)
    except Exception:
        return response.text or "(empty body)"


def _normalize_hit(item: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if "uuid" in item:
        out["uuid"] = item["uuid"]
    elif "id" in item:
        out["uuid"] = item["id"]
    for key in ("content", "score", "monad_id"):
        if key in item:
            out[key] = item[key]
    return out


class TelosClient:
    """HTTP client; each public method opens its own AsyncClient for the request."""

    def __init__(self, base_url: str, *, timeout: float = 60.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def write(
        self,
        monad_id: str,
        content: str,
        parent_ids: list[str] | None = None,
    ) -> dict[str, str]:
        payload = {
            "monad_id": monad_id,
            "content": content,
            "parent_ids": parent_ids or [],
        }
        async with httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
        ) as http:
            try:
                r = await http.post("/api/v1/write", json=payload)
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                detail = _error_detail(e.response)
                raise ValueError(f"Telos API error: {e.response.status_code} {detail}") from e

            data = r.json()
        uuid = data.get("uuid") or data.get("id") if isinstance(data, dict) else None
        if not uuid:
            msg = f"Telos write response missing uuid/id: {data!r}"
            raise ValueError(msg)
        return {"uuid": str(uuid), "status": "ok"}

    async def search(self, monad_id: str, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        payload = {"monad_id": monad_id, "query": query, "top_k": top_k}
        async with httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
        ) as http:
            try:
                r = await http.post("/api/v1/search", json=payload)
                r.raise_for_status()
            except httpx.HTTPStatusError as e:
                detail = _error_detail(e.response)
                raise ValueError(f"Telos API error: {e.response.status_code} {detail}") from e

            response_data = r.json()

        if isinstance(response_data, dict):
            raw_hits = response_data.get("results", [])
        elif isinstance(response_data, list):
            raw_hits = response_data
        else:
            raw_hits = []

        if not isinstance(raw_hits, list):
            raw_hits = []

        normalized: list[dict[str, Any]] = []
        for item in raw_hits:
            if isinstance(item, dict):
                normalized.append(_normalize_hit(item))
        return normalized

    async def probe_reachable(self) -> str:
        """Return success message if Core responds, else an error message."""
        async with httpx.AsyncClient(
            base_url=self._base_url,
            timeout=10.0,
        ) as http:
            errors: list[str] = []
            for path in ("/health", "/"):
                try:
                    r = await http.get(path)
                    if r.is_success:
                        return f"Telos Core is reachable at {self._base_url}"
                    errors.append(f"{path}: HTTP {r.status_code}")
                except httpx.RequestError as e:
                    errors.append(f"{path}: {e}")
        return "Telos Core is not reachable. " + "; ".join(errors)
