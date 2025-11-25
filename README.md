 Model Context Protocol (MCP) streamable HTTP server for natural language access to data.gouv.fr datasets, built with [FastMCP](https://github.com/jlowin/fastmcp) and using Streamable HTTP transport protocol.

### Setup and Configuration

1. **Start the real Hydra CSV database locally:**

   First, you need to have Hydra CSV database running locally. See the [Hydra repository](https://github.com/datagouv/hydra) for instructions on how to set it up. Make sure the Hydra CSV database is accessible on `localhost:5434`.

2. **Start PostgREST pointing to your local Hydra database:**
   ```shell
   docker compose --profile hydra up -d
   ```
   The `--profile hydra` flag tells Docker Compose to start the PostgREST service configured for the real Hydra CSV database. This starts PostgREST on port 8080, connecting to your local Hydra CSV database.

3. **Configure the API endpoint:**
   ```shell
   export PGREST_ENDPOINT="http://localhost:8080"
   ```

4. **Start the HTTP MCP server:**

   The port must be specified via the `MCP_PORT` environment variable:
   ```bash
   MCP_PORT=8007 uv run api_tabular/mcp/server.py
   ```

> Note (production): For production deployments, run behind a TLS reverse proxy. Use environment variables to configure the host and port (e.g., `HOST=0.0.0.0 MCP_PORT=8007 uv run api_tabular/mcp/server.py`). Optionally restrict allowed origins and add token authentication at the proxy level.

### 🚀 Quick Start

1. **Test the server:**
   ```bash
   curl -X POST http://127.0.0.1:8007/mcp -H "Accept: application/json" -H "Content-Type: application/json" -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}'
   ```

### 🔧 MCP client configuration

The MCP server configuration depends on your client. Use the appropriate configuration format for your client:

> **Note:** If you want to create or modify datasets/resources, you'll need a data.gouv.fr API key. You can get one from your [profile settings](https://www.data.gouv.fr/fr/account/). Add it to your client configuration as shown in the examples below.

#### Gemini CLI

```bash
gemini mcp add --transport http api-tabular http://127.0.0.1:8007/mcp
```

Alternatively, add the following to your `~/.gemini/settings.json` file:

```json
{
  "mcpServers": {
    "api-tabular": {
      "httpUrl": "http://127.0.0.1:8007/mcp",
      "args": {
        "apiKey": "your-data-gouv-api-key-here"
      }
    }
  }
}
```

#### Claude Desktop

Add the following to your Claude Desktop configuration file (typically `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS, or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "data-gouv": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://127.0.0.1:8007/mcp",
        "--header",
        "X-MCP-Config: {\"apiKey\":\"your-data-gouv-api-key-here\"}"
      ]
    }
  }
}
```

Or if your client supports direct configuration:

```json
{
  "mcpServers": {
    "data-gouv": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://127.0.0.1:8007/mcp"
      ],
      "config": {
        "apiKey": "your-data-gouv-api-key-here"
      }
    }
  }
}
```

#### VS Code

Add the following to your VS Code `settings.json`:

```json
{
  "servers": {
    "data-gouv": {
      "url": "http://127.0.0.1:8007/mcp",
      "type": "http",
      "config": {
        "apiKey": "your-data-gouv-api-key-here"
      }
    }
  }
}
```

#### Windsurf

Add the following to your `~/.codeium/mcp_config.json`:

```json
{
  "mcpServers": {
    "data-gouv": {
      "serverUrl": "http://127.0.0.1:8007/mcp",
      "config": {
        "apiKey": "your-data-gouv-api-key-here"
      }
    }
  }
}
```

#### Cursor

Cursor supports MCP servers through its settings. To configure the server:

1. Open Cursor Settings (Cmd/Ctrl + ,)
2. Search for "MCP" or "Model Context Protocol"
3. Add a new MCP server with the following configuration:

```json
{
  "mcpServers": {
    "data-gouv": {
      "url": "http://127.0.0.1:8007/mcp",
      "transport": "http",
      "config": {
        "apiKey": "your-data-gouv-api-key-here"
      }
    }
  }
}
```

**Note:**
- Replace `http://127.0.0.1:8007/mcp` with your actual server URL if running on a different host or port. For production deployments, use `https://` and configure the appropriate hostname.
- Replace `your-data-gouv-api-key-here` with your actual API key from [data.gouv.fr account settings](https://www.data.gouv.fr/fr/account/).
- The API key is only required for tools that create or modify datasets/resources. Read-only operations (like `search_datasets`) work without an API key.

### 🧭 Test with MCP Inspector

Use the official MCP Inspector to interactively test the server tools and resources.

Prerequisites:
- Node.js with `npx` available

Steps:
1. Start the MCP server (see above):
   ```bash
   uv run api_tabular/mcp/server.py
   ```
2. In another terminal, launch the inspector with the provided config:
   ```bash
   npx @modelcontextprotocol/inspector --config ./api_tabular/mcp/mcp_config.json --server api-tabular
   ```
   - This connects to `http://127.0.0.1:8007/mcp` as defined in `api_tabular/mcp/mcp_config.json`.
   - If the server port changes, update the config file accordingly.

### 🚚 Transport support

This MCP server uses FastMCP and implements the Streamable HTTP transport only.
STDIO and SSE are not supported.

Use Streamable HTTP at `http://127.0.0.1:8007/mcp` in clients (e.g. MCP Inspector).

### 📋 Available Endpoints

**Streamable HTTP transport (standards-compliant):**
- `POST /mcp` - JSON-RPC messages (client → server)

### 🛠️ Available Tools

The MCP server provides tools to interact with data.gouv.fr datasets:

- **`search_datasets`** - Search for datasets on data.gouv.fr by keywords. Returns a list of datasets matching the search query with their metadata, including title, description, organization, tags, and resource count. Use this to discover datasets before querying their data.

  Parameters:
  - `query` (required): Search query string (searches in title, description, tags)
  - `page` (optional, default: 1): Page number
  - `page_size` (optional, default: 20, max: 100): Number of results per page

### 🧪 Test the MCP server

```bash
# Test the HTTP MCP server
uv run python api_tabular/mcp/test_mcp.py
```

