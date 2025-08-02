"""Handler for patching text file contents."""

import json
import logging
import os
import traceback
from typing import Any, Dict, Sequence

from mcp.types import TextContent, Tool

from mcp_text_editor.handlers.base import BaseHandler

logger = logging.getLogger("mcp-text-editor")


class PatchTextFileContentsHandler(BaseHandler):
    """Handler for patching a text file."""

    name = "patch_text_file_contents"
    description = "Apply patches to text files with string-based validation. Use old_string to specify exact content to replace and new_string for replacement. Supports multi-range patches."

    def get_tool_description(self) -> Tool:
        """Get the tool description."""
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "files": {
                        "type": "array",
                        "description": "List of file operations",
                        "items": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Path to the file. File path must be absolute.",
                                },
                                "encoding": {
                                    "type": "string",
                                    "description": "Text encoding (default: 'utf-8')",
                                    "default": "utf-8",
                                },
                                "patches": {
                                    "type": "array",
                                    "description": "Patches to apply",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "old_string": {
                                                "type": "string",
                                                "description": "Expected content to be replaced",
                                            },
                                            "new_string": {
                                                "type": "string",
                                                "description": "New content to replace with",
                                            },
                                            "ranges": {
                                                "type": "array",
                                                "description": "Line ranges where this patch applies",
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
                                        "required": ["old_string", "new_string", "ranges"],
                                    },
                                },
                            },
                            "required": ["file_path", "patches"],
                        },
                    },
                },
                "required": ["files"],
            },
        )

    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Execute the tool with given arguments."""
        try:
            if "files" not in arguments:
                raise RuntimeError("Missing required argument: files")

            files = arguments["files"]
            if not isinstance(files, list) or len(files) == 0:
                raise RuntimeError("files must be a non-empty list")

            results = []
            
            for file_op in files:
                file_path = file_op["file_path"]
                if not os.path.isabs(file_path):
                    raise RuntimeError(f"File path must be absolute: {file_path}")

                # Check if file exists
                if not os.path.exists(file_path):
                    raise RuntimeError(f"File does not exist: {file_path}")

                encoding = file_op.get("encoding", "utf-8")
                patches = file_op["patches"]

                # Apply patches using the new editor method
                result = await self.editor.edit_file_contents_v2(
                    file_path=file_path,
                    patches=patches,
                    encoding=encoding,
                )
                
                results.append({
                    "file_path": file_path,
                    "result": result
                })

            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Error processing request: {str(e)}") from e
