# Telos MCP Server

Telos Core（FastAPI）をラップし、Claude Code / Claude Desktop などの MCP クライアントから共有メモリに読み書きするサーバーです。

## Local Setup

### 仮想環境と依存関係

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 環境変数（`.env`）

プロジェクト直下に `.env` を置き、少なくとも次を設定します。

| 変数 | 必須 | 説明 |
|------|------|------|
| `TELOS_BASE_URL` | はい | Telos Core のベース URL（例: `https://xxx.up.railway.app`） |
| `TELOS_DEFAULT_MONAD_ID` | いいえ | 省略時の monad ID（デフォルト: `mcp-monad`） |
| `TELOS_DEFAULT_TOP_K` | いいえ | 検索の既定件数（デフォルト: `5`） |

`config.py` が `python-dotenv` で `.env` を読み込みます。

### ローカル起動（stdio）

Claude Desktop など、stdio で接続する場合の例です。

```bash
python server.py
```

デフォルトのトランスポートは `stdio` です。HTTP で試す場合は「Deploy to Railway」や `python server.py --help` を参照してください。

## Test

MCP を起動せずに `client.py` 経由で Core へ疎通・書き込み・検索を確認するスクリプトです。

```bash
python test_local.py
```

事前に `.env` に有効な `TELOS_BASE_URL` を設定してください。

## Deploy to Railway

### Railway CLI でのデプロイ（概要）

1. [Railway CLI](https://docs.railway.com/guides/cli) をインストールし、`railway login` でログインする。
2. このリポジトリで `railway init`（新規プロジェクト）または既存プロジェクトに `railway link` する。
3. ダッシュボードまたは CLI で環境変数を設定する（下記「必要な環境変数」）。
4. `git push` で連携している場合は自動ビルド、または `railway up` でデプロイする。

`Procfile` の `web` プロセスが `streamable-http` モードで起動し、MCP の HTTP エンドポイントは **`/mcp`**（FastMCP 既定）です。ルート **`/`** はヘルスチェック用に `{"status":"ok"}` を返します。

### 必要な環境変数

| 変数 | 必須 | 説明 |
|------|------|------|
| `TELOS_BASE_URL` | はい | Telos Core の URL |
| `TELOS_DEFAULT_MONAD_ID` | いいえ | 既定 monad ID（省略時 `mcp-monad`） |
| `TELOS_DEFAULT_TOP_K` | いいえ | 検索の既定件数（省略時 `5`） |

Railway では `PORT` が自動注入されます（`server.py` の `--port` で使用）。

## Connect to Claude Code

### リモート接続（Railway デプロイ後）

デプロイ先の URL に合わせて `url` を書き換えてください（末尾は `/mcp`）。

```json
{
  "mcpServers": {
    "telos": {
      "type": "http",
      "url": "https://your-telos-mcp.up.railway.app/mcp"
    }
  }
}
```

### ローカル接続（stdio）

`args` のパスは、このリポジトリ内の `server.py` の**絶対パス**に置き換えてください。`TELOS_BASE_URL` は実際の Telos Core の URL に置き換えます。

```json
{
  "mcpServers": {
    "telos": {
      "command": "python",
      "args": ["/absolute/path/to/telos-mcp/server.py"],
      "env": {
        "TELOS_BASE_URL": "https://your-telos.up.railway.app"
      }
    }
  }
}
```

`python` が仮想環境のものを指すようにするか、`command` に `.venv/bin/python` の絶対パスを指定しても構いません。
