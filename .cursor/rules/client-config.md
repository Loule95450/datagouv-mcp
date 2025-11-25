# MCP Client Configuration Guide

Use this guide to wire the data.gouv.fr MCP server into popular MCP-aware clients. The examples assume the server runs on `http://127.0.0.1:8007/mcp`; adjust host/port accordingly. Make sure your `.env` selects the same environment (`DATAGOUV_API_ENV=demo|prod`) that matches the API key you provide below.

## API Key Policy

- Keys must be generated from **https://demo.data.gouv.fr/fr/account/** or **https://www.data.gouv.fr/fr/account/** (match the host to your `DATAGOUV_API_ENV`).
- Each client must send the key in the MCP request payload (the server does **not** fall back to environment variables).
- The key is passed as the `api_key` argument of the `create_dataset` tool. Many clients allow you to preconfigure this via `"config": {"apiKey": "..."}`.

If the API responds with `401 Invalid API Key`, double-check that the key belongs to the demo environment—production keys (`www.data.gouv.fr`) are rejected.

## Cursor

```json
{
  "mcpServers": {
    "data-gouv": {
      "url": "http://127.0.0.1:8007/mcp",
      "transport": "http",
      "config": {
        "apiKey": "YOUR_DEMO_API_KEY"
      }
    }
  }
}
```

Cursor will automatically include `config.apiKey` when calling MCP tools, so `create_dataset` receives it as the `api_key` parameter.

## Windsurf / Codeium MCP

Edit `~/.codeium/mcp_config.json`:

```json
{
  "mcpServers": {
    "data-gouv": {
      "serverUrl": "http://127.0.0.1:8007/mcp",
      "config": {
        "apiKey": "YOUR_DEMO_API_KEY"
      }
    }
  }
}
```

## VS Code MCP extension

Add to `settings.json`:

```json
{
  "servers": {
    "data-gouv": {
      "url": "http://127.0.0.1:8007/mcp",
      "type": "http",
      "config": {
        "apiKey": "YOUR_DEMO_API_KEY"
      }
    }
  }
}
```

## Gemini CLI

```bash
gemini mcp add --transport http data-gouv http://127.0.0.1:8007/mcp
```

Then edit `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "data-gouv": {
      "httpUrl": "http://127.0.0.1:8007/mcp",
      "args": {
        "apiKey": "YOUR_DEMO_API_KEY"
      }
    }
  }
}
```

## Claude Desktop

Claude supports running MCP servers through `mcp-remote`:

```json
{
  "mcpServers": {
    "data-gouv": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://127.0.0.1:8007/mcp",
        "--header",
        "X-MCP-Config: {\"apiKey\":\"YOUR_DEMO_API_KEY\"}"
      ]
    }
  }
}
```

## Notes

- If a client repeatedly shows the old API key, restart it so it reloads the MCP config (Cursor caches configs until restart).
- For production deployments, use HTTPS, set `DATAGOUV_API_ENV=prod`, and configure the reverse proxy to forward the same `apiKey` payload; nothing changes server-side.
- `search_datasets` does not need an API key, so read-only workflows work without configuration.


