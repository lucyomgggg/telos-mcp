# telos-mcp Architecture

最終更新: 2026-04-18

`telos-mcp` は transport adapter です。  
この repo 自身は保存責務を持たず、`telos-core` の REST 契約を MCP tool へ変換することだけを担当します。

## 1. 原則

- source of truth は常に `telos-core`
- `telos-mcp` は schema や DB を持たない
- 変換ロジックは薄く、設定と transport を分離する

## 2. 現在の構成

```text
server.py
  -> telos_mcp/server.py
    -> telos_mcp/tools.py
    -> telos_mcp/client.py
    -> telos_mcp/settings.py
```

- `server.py`
  - 後方互換の entrypoint
- `telos_mcp/settings.py`
  - environment から設定を読む
- `telos_mcp/client.py`
  - `telos-core` REST client
- `telos_mcp/tools.py`
  - MCP tool 定義
- `telos_mcp/server.py`
  - FastMCP instance
  - well-known routes
  - transport 設定

## 3. 変更ルール

1. tool を足す前に `telos-core` 側に正規 API があることを確認する。
2. `telos-mcp` 独自の保存や検索ロジックを追加しない。
3. 互換 shim は root に置いてよいが、本体ロジックは `telos_mcp/` 配下へ集約する。
