"""Handler for inserting content into text files."""

import json
import logging
import os
import traceback
from typing import Any, Dict, Sequence

from mcp.types import TextContent, Tool

from mcp_text_editor.handlers.base import BaseHandler

logger = logging.getLogger("mcp-text-editor")


class InsertTextFileContentsHandler(BaseHandler):
    """Handler for inserting content before or after a specific line in a text file."""

    name = "insert_text_file_contents"
    description = "Insert content before or after a specific line in a text file with context validation. Supports batch insertions with context_line validation at insertion points."

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
                    "insertions": {
                        "type": "array",
                        "description": "List of insertion operations",
                        "items": {
                            "type": "object",
                            "properties": {
                                "content_to_insert": {
                                    "type": "string",
                                    "description": "Content to insert",
                                },
                                "position": {
                                    "type": "string",
                                    "enum": ["before", "after"],
                                    "description": "Position relative to reference line ('before' or 'after')",
                                },
                                "context_line": {
                                    "type": "string",
                                    "description": "Expected content of the reference line for validation",
                                },
                                "line_number": {
                                    "type": "integer",
                                    "description": "Line number of the reference line",
                                },
                            },
                            "required": ["content_to_insert", "position", "context_line", "line_number"],
                        },
                    },
                    "encoding": {
                        "type": "string",
                        "description": "Text encoding (default: 'utf-8')",
                        "default": "utf-8",
                    },
                    "require_exact_match": {
                        "type": "boolean",
                        "description": "Whether to require exact whitespace matching. Default is false, which ignores leading and trailing whitespace on each line when matching context_line against file content. If true, users MUST carefully count and ensure that the number and type of whitespaces on each line matches the existing text exactly.",
                        "default": False,
                    },
                },
                "required": ["file_path", "insertions"],
            },
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Execute the tool with given arguments."""
        try:
            if "file_path" not in arguments:
                raise RuntimeError("Missing required argument: file_path")
            if "insertions" not in arguments:
                raise RuntimeError("Missing required argument: insertions")

            file_path = arguments["file_path"]
            if not os.path.isabs(file_path):
                raise RuntimeError(f"File path must be absolute: {file_path}")

            insertions = arguments["insertions"]
            if not isinstance(insertions, list) or len(insertions) == 0:
                raise RuntimeError("insertions must be a non-empty list")

            encoding = arguments.get("encoding", "utf-8")
            require_exact_match = arguments.get("require_exact_match", False)

            # Validate insertion operations
            for i, insertion in enumerate(insertions):
                if not isinstance(insertion, dict):
                    raise RuntimeError(f"Insertion {i} must be an object")
                
                required_fields = ["content_to_insert", "position", "context_line", "line_number"]
                for field in required_fields:
                    if field not in insertion:
                        raise RuntimeError(f"Insertion {i} missing required field: {field}")
                
                if insertion["position"] not in ["before", "after"]:
                    raise RuntimeError(f"Insertion {i} position must be 'before' or 'after'")
                
                if not isinstance(insertion["line_number"], int) or insertion["line_number"] < 1:
                    raise RuntimeError(f"Insertion {i} line_number must be a positive integer")

            # Check if file exists after validation
            if not os.path.exists(file_path):
                raise RuntimeError(f"File does not exist: {file_path}")

            # Get result from editor using the new v2 method
            result = await self.editor.insert_text_file_contents_v2(
                file_path=file_path,
                insertions=insertions,
                encoding=encoding,
                require_exact_match=require_exact_match,
            )
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Error processing request: {str(e)}") from e
