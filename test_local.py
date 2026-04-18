"""Local integration checks for client.TelosClient (no MCP server)."""

from __future__ import annotations

import asyncio
import traceback
from datetime import datetime

from dotenv import load_dotenv

from client import TelosClient
from config import load_settings


async def main() -> None:
    load_dotenv()

    try:
        settings = load_settings()
    except ValueError as e:
        print(f"[config] {e}")
        print("All tests completed.")
        return

    base = settings.telos_base_url
    client = TelosClient(base)

    # 1. telos_status 相当: 疎通確認
    print("--- 1. connectivity (probe_reachable) ---")
    try:
        status_msg = await client.probe_reachable()
        print(status_msg)
    except Exception as e:
        print(f"Error: {e!r}")
        traceback.print_exc()
        print("Skipping write and search.")
        print("All tests completed.")
        return

    if "Telos Core is reachable at" not in status_msg:
        print("Connectivity check did not succeed. Skipping write and search.")
        print("All tests completed.")
        return

    # 2–3. telos_write + UUID 表示
    print("--- 2–3. write ---")
    content = f"MCP サーバーからのテスト書き込み。{datetime.now().isoformat()}"
    try:
        result = await client.write(
            monad_id="test-monad",
            content=content,
            parent_ids=None,
        )
        uuid = result["uuid"]
        print(f"UUID: {uuid}")
    except Exception as e:
        print(f"Error: {e!r}")
        traceback.print_exc()
        print("Skipping search.")
        print("All tests completed.")
        return

    # 4. telos_search
    print("--- 4. search ---")
    try:
        hits = await client.search(monad_id="test-monad", query="テスト", limit=5)
        print(f"hits ({len(hits)}): {hits}")
    except Exception as e:
        print(f"Error: {e!r}")
        traceback.print_exc()

    print("All tests completed.")


if __name__ == "__main__":
    asyncio.run(main())
