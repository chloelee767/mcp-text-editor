"""Argument parser for the MCP Text Editor Server."""

import argparse

def create_argument_parser() -> argparse.ArgumentParser:
    """Creates and configures the argument parser."""
    parser = argparse.ArgumentParser(
        description="MCP Text Editor Server"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["claude-code"],
        default=None,
        help="Set the server mode.",
    )
    return parser
