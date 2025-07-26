#!/usr/bin/env python3
"""
Simple CLI tool for calling MCP server tools directly.
Usage: python call_mcp_tool.py --name tool-name --payload-file request.json
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def call_mcp_tool(server_command: list[str], tool_name: str, payload: dict):
    """Call a tool on an MCP server and return the result."""
    
    server_params = StdioServerParameters(
        command=server_command[0],
        args=server_command[1:] if len(server_command) > 1 else None,
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # Call the tool
            result = await session.call_tool(tool_name, payload)
            return result


def main():
    parser = argparse.ArgumentParser(description='Call MCP server tools from command line')
    parser.add_argument('--name', required=True, help='Tool name to call')
    parser.add_argument('--payload-file', required=True, help='JSON file containing tool payload')
    parser.add_argument('--server-command', default='mcp_text_editor',
                       help='Command to start MCP server (default: mcp_text_editor)')
    
    args = parser.parse_args()
    
    # Load payload from file
    try:
        with open(args.payload_file, 'r') as f:
            payload = json.load(f)
    except FileNotFoundError:
        print(f"Error: Payload file '{args.payload_file}' not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in payload file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Parse server command
    server_command = args.server_command.split()
    
    # Call the tool
    try:
        result = asyncio.run(call_mcp_tool(server_command, args.name, payload))
        print(json.dumps(result.content, indent=2))
    except Exception as e:
        print(f"Error calling tool: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
