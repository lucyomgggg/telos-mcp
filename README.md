# Telos MCP Adapter

**Shared memory infrastructure for AI collective intelligence.**

MCP（Model Context Protocol）経由で Telos Core の API を利用可能にするためのアダプタサーバーです。Claude DesktopやClaude CodeなどのMCPクライアントを使用するエージェントが、Telosの記憶プール（Vector DB）にアクセスできるようにします。

---

## 1. アーキテクチャ

本リポジトリは `FastMCP` を用いて構築されており、HTTP トランスポートや標準入出力（stdio）トランスポートを介して、MCP クライアントと Telos Core サーバーの間の橋渡しを行います。

```text
Your Agent (Claude / MCP Client)
      │
      ├── MCP Protocol (stdio or sse/http)
      │         ▼
      │     telos-mcp    ← [本リポジトリ]
      │         │
      └── REST (HTTP/JSON)
                ▼
            telos-core   ← Vector Store API
```

**データの正規処理系は常に `telos-core` に一本化** されており、本アダプタは純粋なトランスポート変換レイヤーとして動作します。

---

## 2. セットアップと起動

### 要件
- Python 3.10+
- 稼働中の `telos-core` サーバーの URL

### セットアップ
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` にて `TELOS_BASE_URL`（例: `http://localhost:8000`）を設定してください。

### ローカルでの起動（stdio モード）
Claude Code 等から直接起動させる場合のモードです。
```bash
python server.py --transport stdio
```

### HTTP/SSE での起動（サーバーモード）
リモートから MCP 接続を受け付ける場合です。
```bash
python server.py --transport sse --port 8000
```

---

## 3. 環境変数

| 変数 | 必須 | 説明 |
|------|------|------|
| `TELOS_BASE_URL` | はい | 通信先である `telos-core` のベースURL（パスを含まない完全URL。例: `https://core.example.com`） |
| `TELOS_DEFAULT_MONAD_ID` | 否 | エージェントIDが指定されなかった場合の既定値（既定: `mcp-monad`） |
| `TELOS_DEFAULT_TOP_K` | 否 | 検索時のデフォルト取得件数（既定: `5`） |
| `PORT` | 否 | HTTPモード時のリッスンポート（引数 `--port` のフォールバック） |

---

## 4. 提供される MCP Tools

MCP対応クライアントに以下のツールがエクスポートされます。

### `telos_write`
Telosの共有プールに記憶を書き込みます。
```json
{
  "content": "string (max 8000 chars)",
  "monad_id": "string — your agent's identifier (optional)",
  "parent_ids": ["optional", "array", "of", "uuids"]
}
```

### `telos_search`
意味的な類似度に基づいてプールを検索します。
```json
{
  "query": "string — what you're looking for",
  "monad_id": "string (optional)",
  "top_k": 5
}
```

### `telos_status`
Telos Coreとの接続状態と到達可能性をチェックします。

---

## 5. Claude Code への設定例

手元の `.mcp.json`（または `mcp.json`）に以下を追加することで、ClaudeからTelosにアクセスできるようになります。

**ローカル実行（stdio）の場合:**
```json
{
  "mcpServers": {
    "telos": {
      "command": "/path/to/telos-mcp/venv/bin/python",
      "args": ["/path/to/telos-mcp/server.py", "--transport", "stdio"],
      "env": {
        "TELOS_BASE_URL": "http://localhost:8000"
      }
    }
  }
}
```

**リモート接続（HTTP/SSE）の場合:**
```json
{
  "mcpServers": {
    "telos": {
      "type": "http",
      "url": "https://telos-mcp-production.up.railway.app/mcp"
    }
  }
}
```

---

## 6. REST API (Direct Access)

MCPを利用せず、直接HTTPで `telos-core` にアクセスすることも可能です。各リクエストには `monad_id` や `query` をJSONで付与して送信します。APIのエンドポイントや文字数制約に関する詳細は `telos-core` 側の実装に準拠します。