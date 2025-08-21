"""Handler for appending content to text files."""

import json
import logging
import os
import traceback
from typing import Any, Dict, Sequence

from mcp.types import TextContent, Tool

from mcp_text_editor.handlers.base import BaseHandler
from mcp_text_editor.models import AppendTextFileContentsRequestV2

logger = logging.getLogger("mcp-text-editor")


class AppendTextFileContentsHandler(BaseHandler):
    """Handler for appending content to an existing text file."""

    name = "append_text_file_contents"
    description = "Append content to an existing text file. The file must exist."

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
                    "content_to_append": {
                        "type": "string",
                        "description": "Content to append to the file",
                    },
                    "expected_file_ending": {
                        "type": "string",
                        "description": "Expected content of the final line for validation",
                    },
                    "encoding": {
                        "type": "string",
                        "description": "Text encoding (default: 'utf-8')",
                        "default": "utf-8",
                    },
                    "require_exact_match": {
                        "type": "boolean",
                        "description": "Whether to require exact whitespace matching. Default is false, which ignores leading and trailing whitespace on each line when matching expected_file_ending against file content. If true, users MUST carefully count and ensure that the number and type of whitespaces on each line matches the existing text exactly.",
                        "default": False,
                    },
                },
                "required": ["file_path", "content_to_append", "expected_file_ending"],
            },
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Execute the tool with given arguments."""
        try:
            # Get require_exact_match parameter
            require_exact_match = arguments.get("require_exact_match", False)
            
            # Validate arguments using the model
            request = AppendTextFileContentsRequestV2(**arguments)
            
            if not os.path.isabs(request.file_path):
                raise RuntimeError(f"File path must be absolute: {request.file_path}")

            # Check if file exists
            if not os.path.exists(request.file_path):
                raise RuntimeError(f"File does not exist: {request.file_path}")

            # Use the new v2 method for string-based validation
            result = await self.editor.append_text_file_contents_v2(
                file_path=request.file_path,
                content_to_append=request.content_to_append,
                expected_file_ending=request.expected_file_ending,
                encoding=request.encoding,
                require_exact_match=require_exact_match,
            )

            # Check if the operation resulted in an error
            if result.get("result") == "error":
                raise RuntimeError(result.get("reason", "Unknown error occurred"))

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Error processing request: {str(e)}") from e
