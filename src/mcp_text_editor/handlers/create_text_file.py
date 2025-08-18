"""Handler for creating new text files."""

import json
import logging
import os
import traceback
from typing import Any, Dict, Sequence

from mcp.types import TextContent, Tool

from mcp_text_editor.handlers.base import BaseHandler

logger = logging.getLogger("mcp-text-editor")


class CreateTextFileHandler(BaseHandler):
    """Handler for creating a new text file."""

    name = "create_text_file"
    description = (
        "Create a new text file with given content. The file must not exist already."
    )

    def get_tool_description(self) -> Tool:
        """Get the tool description."""
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the text file. File path must be absolute.",
                    },
                    "contents": {
                        "type": "string",
                        "description": "Content to write to the file",
                    },
                    "encoding": {
                        "type": "string",
                        "description": "Text encoding (default: 'utf-8')",
                        "default": "utf-8",
                    },
                },
                "required": ["file_path", "contents"],
            },
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Execute the tool with given arguments."""
        try:
            if "file_path" not in arguments:
                raise RuntimeError("Missing required argument: file_path")
            if "contents" not in arguments:
                raise RuntimeError("Missing required argument: contents")

            file_path = arguments["file_path"]
            if not os.path.isabs(file_path):
                raise RuntimeError(f"File path must be absolute: {file_path}")

            # Check if file already exists
            if os.path.exists(file_path):
                raise RuntimeError(f"File already exists: {file_path}")

            encoding = arguments.get("encoding", "utf-8")
            contents = arguments["contents"]

            # Create parent directories if they don't exist
            parent_dir = os.path.dirname(file_path)
            if parent_dir:
                try:
                    os.makedirs(parent_dir, exist_ok=True)
                except OSError as e:
                    raise RuntimeError(f"Failed to create directory: {str(e)}")

            # Write the file directly
            with open(file_path, "w", encoding=encoding) as f:
                f.write(contents)
            
            result = {
                "result": "ok",
                "message": f"File created successfully: {file_path}"
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Error processing request: {str(e)}") from e
