"""MCP Text Editor Server package."""

import asyncio

from .args import create_argument_parser
from .server import main
from .text_editor import TextEditor

# Create a global text editor instance
_text_editor = TextEditor()


def run() -> None:
    """Run the MCP Text Editor Server."""
    parser = create_argument_parser()
    args = parser.parse_args()
    asyncio.run(main(args))
