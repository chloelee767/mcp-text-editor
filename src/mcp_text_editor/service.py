"""Core service logic for the MCP Text Editor Server."""

from typing import Dict, List, Optional, Tuple

from mcp_text_editor.models import (
    EditFileOperation,
    EditPatch,
    EditResult,
    FileRange,
)


class TextEditorService:
    """Service class for text file operations."""


    @staticmethod
    def read_file_contents(
        file_path: str, start: int = 1, end: Optional[int] = None
    ) -> Tuple[str, int, int]:
        """Read file contents within specified line range."""
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Adjust line numbers to 0-based index
        start = max(1, start) - 1
        end = len(lines) if end is None else min(end, len(lines))

        selected_lines = lines[start:end]
        content = "".join(selected_lines)

        return content, start + 1, end

    @staticmethod
    def validate_patches(patches: List[EditPatch], total_lines: int) -> bool:
        """Validate patches for overlaps and bounds."""
        # Sort patches by start
        sorted_patches = sorted(patches, key=lambda x: x.start)

        prev_end = 0
        for patch in sorted_patches:
            if patch.start <= prev_end:
                return False
            patch_end = patch.end or total_lines
            if patch_end > total_lines:
                return False
            prev_end = patch_end

        return True



    @staticmethod
    def validate_ranges(ranges: List[FileRange], total_lines: int) -> bool:
        """Validate ranges for overlaps and bounds."""
        # Sort ranges by start line
        sorted_ranges = sorted(ranges, key=lambda x: x.start)

        prev_end = 0
        for range_ in sorted_ranges:
            if range_.start <= prev_end:
                return False  # Overlapping ranges
            if range_.start < 1:
                return False  # Invalid start line
            range_end = range_.end or total_lines
            if range_end > total_lines:
                return False  # Exceeding file length
            if range_.end is not None and range_.end < range_.start:
                return False  # End before start
            prev_end = range_end

        return True
