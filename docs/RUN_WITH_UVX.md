# Running Tidal MCP with uvx

This Tidal MCP server can be run directly from the repository using `uvx`, similar to the Spotify MCP.

## Prerequisites

1. Install `uv` if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Ensure you have your Tidal credentials ready (optional - uses default if not provided):
   - `TIDAL_CLIENT_ID`
   - `TIDAL_CLIENT_SECRET`

## Running the Server

### From the repository directory:

```bash
cd /path/to/tidal-mcp
uvx --from . tidal-mcp
```

### Or run directly using Python module:

```bash
cd /path/to/tidal-mcp
python -m tidal_mcp
```

### Or install and run:

```bash
cd /path/to/tidal-mcp
pip install -e .
tidal-mcp
```

## Using with Claude Desktop

To configure this MCP server with Claude Desktop, add the following to your Claude configuration:

```json
{
  "mcpServers": {
    "tidal": {
      "command": "uvx",
      "args": ["--from", "/path/to/tidal-mcp", "tidal-mcp"],
      "env": {
        "TIDAL_CLIENT_ID": "your-client-id",  # pragma: allowlist secret
        "TIDAL_CLIENT_SECRET": "your-client-secret"  # pragma: allowlist secret
      }
    }
  }
}
```

## Environment Variables

The server supports the following environment variables:

- `TIDAL_CLIENT_ID`: Your Tidal API client ID (optional)
- `TIDAL_CLIENT_SECRET`: Your Tidal API client secret (optional)
- `TIDAL_QUALITY`: Audio quality setting (optional)
- `TIDAL_COUNTRY_CODE`: Country code for content availability (optional, defaults to US)

## Testing the Installation

To verify the server is working:

```bash
# Test directly
uvx --from . tidal-mcp

# Should output server initialization logs
```

## Development Mode

For development with live reloading:

```bash
# Install in editable mode
pip install -e .

# Run the server
tidal-mcp
```

## Troubleshooting

1. **Module not found error**: Ensure you're in the project root directory
2. **Authentication errors**: Check your Tidal credentials in environment variables
3. **uvx not found**: Ensure uv is installed and in your PATH

## Comparison with Spotify MCP

This setup mirrors the Spotify MCP configuration:
- Both use `uvx` for easy execution from repository
- Both support environment variable configuration
- Both can be integrated with Claude Desktop using similar configuration
