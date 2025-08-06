#!/bin/bash
# Test script for uvx execution

echo "Testing Tidal MCP with uvx..."
echo "================================"

# Test 1: Check if uvx can find the package
echo -e "\nTest 1: Testing uvx package discovery"
echo "Running: uvx --from . tidal-mcp"
echo "(This will start the server, press Ctrl+C to stop)"

echo -e "\n================================"
echo "Setup complete! You can now run:"
echo "  uvx --from . tidal-mcp"
echo ""
echo "Or configure in Claude Desktop by adding to your config:"
echo '
{
  "mcpServers": {
    "tidal": {
      "command": "uvx",
      "args": ["--from", "'$(pwd)'", "tidal-mcp"],
      "env": {
        "TIDAL_CLIENT_ID": "your-client-id",
        "TIDAL_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}'