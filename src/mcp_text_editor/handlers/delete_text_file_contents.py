"""Handler for deleting content from text files."""

import json
import logging
import os
import traceback
from typing import Any, Dict, Sequence

from mcp.types import TextContent, Tool

from mcp_text_editor.handlers.base import BaseHandler
from mcp_text_editor.models import DeleteTextFileContentsRequestV2, DeleteOperation

logger = logging.getLogger("mcp-text-editor")


class DeleteTextFileContentsHandler(BaseHandler):
    """Handler for deleting content from a text file."""

    name = "delete_text_file_contents"
    description = "Delete specified content ranges from a text file with string-based validation. Use expected_content to specify exact content to delete. Supports multi-range deletions."

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
                    "deletions": {
                        "type": "array",
                        "description": "List of deletion operations",
                        "items": {
                            "type": "object",
                            "properties": {
                                "expected_content": {
                                    "type": "string",
                                    "description": "Expected content to be deleted",
                                },
                                "ranges": {
                                    "type": "array",
                                    "description": "Line ranges where this content should be deleted",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "start": {
                                                "type": "integer",
                                                "description": "Starting line number (1-based)",
                                            },
                                            "end": {
                                                "type": ["integer", "null"],
                                                "description": "Ending line number (null for end of file)",
                                            },
                                        },
                                        "required": ["start"],
                                    },
                                },
                            },
                            "required": ["expected_content", "ranges"],
                        },
                    },
                    "encoding": {
                        "type": "string",
                        "description": "Text encoding (default: 'utf-8')",
                        "default": "utf-8",
                    },
                },
                "required": ["file_path", "deletions"],
            },
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Execute the tool with given arguments."""
        try:
            # Validate and parse arguments using models
            try:
                request = DeleteTextFileContentsRequestV2(**arguments)
            except Exception as e:
                raise RuntimeError(f"Invalid request format: {str(e)}") from e

            # Additional validation for absolute path
            if not os.path.isabs(request.file_path):
                raise RuntimeError(f"File path must be absolute: {request.file_path}")

            # Check if file exists
            if not os.path.exists(request.file_path):
                raise RuntimeError(f"File does not exist: {request.file_path}")

            # Convert models to dictionaries for the text editor v2 method
            deletions_data = []
            for deletion in request.deletions:
                deletion_dict = {
                    "expected_content": deletion.expected_content,
                    "ranges": [
                        {"start": r.start, "end": r.end} for r in deletion.ranges
                    ]
                }
                deletions_data.append(deletion_dict)

            # Execute deletion using the new v2 method
            result = await self.editor.delete_text_file_contents_v2(
                file_path=request.file_path,
                deletions=deletions_data,
                encoding=request.encoding,
            )

            return [
                TextContent(type="text", text=json.dumps(result, indent=2))
            ]

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Error processing request: {str(e)}") from e
