"""MCP Text Editor Server implementation."""

import asyncio
import logging
import traceback
from argparse import Namespace
from collections.abc import Sequence
from typing import Any, List

from mcp.server import Server
from mcp.types import TextContent, Tool

from mcp_text_editor.handlers import (
    AppendTextFileContentsHandler,
    CreateTextFileHandler,
    DeleteTextFileContentsHandler,
    GetTextFileContentsHandler,
    InsertTextFileContentsHandler,
    PatchTextFileContentsHandler,
)
from mcp_text_editor.version import __version__

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-text-editor")

app: Server = Server("mcp-text-editor")

# Initialize tool handlers
get_contents_handler = GetTextFileContentsHandler()
patch_file_handler = PatchTextFileContentsHandler()
create_file_handler = CreateTextFileHandler()
append_file_handler = AppendTextFileContentsHandler()
delete_contents_handler = DeleteTextFileContentsHandler()
insert_file_handler = InsertTextFileContentsHandler()

class ToolManager:
    def __init__(self, args: Namespace):
        self.mode = args.mode
        self.all_tools = [
            get_contents_handler.get_tool_description(),
            create_file_handler.get_tool_description(),
            append_file_handler.get_tool_description(),
            delete_contents_handler.get_tool_description(),
            insert_file_handler.get_tool_description(),
            patch_file_handler.get_tool_description(),
        ]
        self.claude_code_tools = [
            patch_file_handler.get_tool_description(),
        ]

    def get_available_tools(self) -> List[Tool]:
        if self.mode == "claude-code":
            return self.claude_code_tools
        return self.all_tools

    async def call_tool(self, name: str, arguments: Any) -> Sequence[TextContent]:
        logger.info(f"Calling tool: {name}")
        try:
            available_tools = [tool.name for tool in self.get_available_tools()]
            if name not in available_tools:
                raise ValueError(f"Unknown tool: {name}")

            if name == get_contents_handler.name:
                return await get_contents_handler.run_tool(arguments)
            elif name == create_file_handler.name:
                return await create_file_handler.run_tool(arguments)
            elif name == append_file_handler.name:
                return await append_file_handler.run_tool(arguments)
            elif name == delete_contents_handler.name:
                return await delete_contents_handler.run_tool(arguments)
            elif name == insert_file_handler.name:
                return await insert_file_handler.run_tool(arguments)
            elif name == patch_file_handler.name:
                return await patch_file_handler.run_tool(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
        except ValueError:
            logger.error(traceback.format_exc())
            raise
        except Exception as e:
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Error executing command: {str(e)}") from e

# Module-level functions for testability
async def list_tools(tool_manager: ToolManager) -> List[Tool]:
    """List available tools."""
    return tool_manager.get_available_tools()


async def call_tool(name: str, arguments: Any, tool_manager: ToolManager) -> Sequence[TextContent]:
    """Handle tool calls."""
    return await tool_manager.call_tool(name, arguments)


async def main(args: Namespace) -> None:
    """Main entry point for the MCP text editor server."""
    logger.info(f"Starting MCP text editor server v{__version__}")
    if args.mode:
        logger.info(f"Server mode: {args.mode}")

    tool_manager = ToolManager(args)

    @app.list_tools()
    async def _list_tools() -> List[Tool]:
        """List available tools."""
        return await list_tools(tool_manager)

    @app.call_tool()
    async def _call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
        """Handle tool calls."""
        return await call_tool(name, arguments, tool_manager)

    try:
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options(),
            )
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise


if __name__ == "__main__":
    from mcp_text_editor.args import create_argument_parser

    parser = create_argument_parser()
    args = parser.parse_args()
    asyncio.run(main(args))
