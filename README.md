# Lanyard MCP Server

A Model Context Protocol (MCP) server that provides Discord user presence information through the Lanyard API.

## Purpose

This MCP server provides a secure interface for AI assistants to retrieve real-time Discord presence data, including online status, Spotify activity, Discord activities, and custom KV data for Discord users via the Lanyard service.

## Features

### Current Implementation

- **`get_user_presence`** - Get complete Discord presence information including status, platform info, Spotify, activities, and KV data
- **`get_user_spotify`** - Get detailed Spotify listening information with track details and timestamps
- **`get_user_kv`** - Retrieve custom Lanyard KV (key-value) data set by the user

All tools include:
- Input sanitization and validation for Discord user IDs
- Formatted, human-readable output with emojis
- Proper error handling for API failures
- Rate limit detection
- Timeout handling

## Prerequisites

- Docker Desktop with MCP Toolkit enabled
- Docker MCP CLI plugin (`docker mcp` command)
- Discord user IDs (17-20 digit numbers) of users who are using Lanyard

## Installation

### Step 1: Build the Docker Image

```bash
docker build -t lanyard-mcp-server:latest .
```

### Step 2: Configure MCP Catalog

Copy the custom catalog configuration:

```bash
# Copy custom.yaml to your Docker MCP catalogs directory
cp custom.yaml ~/.docker/mcp/catalogs/custom.yaml
```

### Step 3: VS Code Integration (Optional)

If using Visual Studio Code with MCP support:

```bash
# Copy the MCP configuration to your project
cp .vscode/mcp.json /path/to/your/project/.vscode/
```

### Step 4: Import and Enable the Server

```bash
# Import the catalog
docker mcp catalog import custom.yaml

# Enable the Lanyard server
docker mcp server enable lanyard
```

## Agent Prompts

When working with AI agents that have access to this MCP server, you can use these example commands:

### Get User Presence Information
```bash
docker mcp tools call get_user_presence user_id=77488778255540224
```

### Get Spotify Activity
```bash
docker mcp tools call get_user_spotify user_id=77488778255540224
```

### Get Custom KV Data
```bash
docker mcp tools call get_user_kv user_id=77488778255540224
```

## Usage Examples

In Claude Desktop, you can ask:

- "What is the Discord presence for user 77488778255540224?"
- "Is user 77488778255540224 listening to Spotify?"
- "Show me the custom KV data for Discord user 77488778255540224"
- "Get the current status and activities for user 77488778255540224"
- "What song is user 77488778255540224 listening to on Spotify?"

## What is Lanyard?

Lanyard is a service that exposes Discord user presence data through a REST API and WebSocket. Users must opt-in by joining the Lanyard Discord server. This MCP server uses the REST API to fetch user presence information.

## Architecture

AI Agent → MCP Gateway → Lanyard MCP Server → Lanyard API ↓ Discord Presence Data

## Development

### Local Testing

```bash
# Run directly
python lanyard_server.py

# Test MCP protocol
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python lanyard_server.py

# Test with a known user ID (Lanyard creator)
echo '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_user_presence","arguments":{"user_id":"94490510688792576"}},"id":2}' | python lanyard_server.py
```

Adding New Tools

1. Add the function to lanyard_server.py
2. Decorate with @mcp.tool()
3. Follow the pattern: single-line docstring, empty string defaults, return formatted string
4. Update the catalog entry with the new tool name
5. Rebuild the Docker image

### Troubleshooting

Tools Not Appearing

- Verify Docker image built successfully: `docker images | grep lanyard`
- Check catalog and registry files in `~/.docker/mcp/catalogs/`
- Ensure Claude Desktop config includes custom catalog
- Restart Claude Desktop completely

"User not found" Errors

- Verify the Discord user ID is correct (17-20 digits)
- Ensure the user has joined the Lanyard Discord server
- Check that the user hasn't opted out of Lanyard

Rate Limit Errors

- Lanyard API has rate limits
- Wait a few moments before retrying
- Consider implementing caching if making frequent requests

### API Reference

This server uses the Lanyard REST API:

- Base URL: https://api.lanyard.rest/v1
- Endpoint: GET /users/:user_id
- Documentation: https://github.com/Phineas/lanyard

Security Considerations

- No authentication required (Lanyard API is public)
- User IDs are validated and sanitized before use
- Running as non-root user in Docker
- Request timeouts prevent hanging
- No sensitive data stored or logged

### Future Enhancement Ideas

- WebSocket support for real-time updates
- Caching to reduce API calls
- Batch user lookups
- Historical presence tracking
- Activity statistics
- Custom formatting options

### Testing

94490510688792576 - Phineas (Lanyard creator)
77488778255540224 - b6d (MCP integration)

Find more users by joining the Lanyard Discord server.

### Limitations

- Requires users to opt-in by joining Lanyard Discord
- Subject to Lanyard API rate limits
- No real-time updates (REST only, not WebSocket)
- Presence data depends on Discord API availability

### Resources

- Lanyard GitHub: https://github.com/Phineas/lanyard
- Lanyard Discord: https://discord.gg/lanyard
- MCP Documentation: https://modelcontextprotocol.io