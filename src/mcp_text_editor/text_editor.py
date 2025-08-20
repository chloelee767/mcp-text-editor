"""Core text editor functionality with file operation handling."""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from mcp_text_editor.models import EditPatch, FileRanges
from mcp_text_editor.service import TextEditorService

logger = logging.getLogger(__name__)


class TextEditor:
    """Handles text file operations with security checks and conflict detection."""

    def __init__(self):
        """Initialize TextEditor."""
        self._validate_environment()
        self.service = TextEditorService()

    def create_error_response(
        self,
        error_message: str,
        file_path: Optional[str] = None,
        suggestion: Optional[str] = None,
        hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a standardized error response.

        Args:
            error_message (str): The error message to include
            file_path (Optional[str], optional): File path to use as dictionary key
            suggestion (Optional[str], optional): Suggested operation type
            hint (Optional[str], optional): Hint message for users

        Returns:
            Dict[str, Any]: Standardized error response structure
        """
        error_response = {
            "result": "error",
            "reason": error_message,
        }

        # Add fields if provided
        if suggestion:
            error_response["suggestion"] = suggestion
        if hint:
            error_response["hint"] = hint

        if file_path:
            return {file_path: error_response}
        return error_response

    def _validate_environment(self) -> None:
        """
        Validate environment variables and setup.
        Can be extended to check for specific permissions or configurations.
        """
        # Future: Add environment validation if needed
        pass  # pragma: no cover

    def _validate_file_path(self, file_path: str | os.PathLike) -> None:
        """
        Validate if file path is allowed and secure.

        Args:
            file_path (str | os.PathLike): Path to validate

        Raises:
            ValueError: If path is not allowed or contains dangerous patterns
        """
        # Convert path to string for checking
        path_str = str(file_path)

        # Check for dangerous patterns
        if ".." in path_str:
            raise ValueError("Path traversal not allowed")


    async def _read_file(
        self, file_path: str, encoding: str = "utf-8"
    ) -> Tuple[List[str], str, int]:
        """Read file and return lines, content, and total lines.

        Args:
            file_path (str): Path to the file to read
            encoding (str, optional): File encoding. Defaults to "utf-8"

        Returns:
            Tuple[List[str], str, int]: Lines, content, and total line count

        Raises:
            FileNotFoundError: If file not found
            UnicodeDecodeError: If file cannot be decoded with specified encoding
        """
        self._validate_file_path(file_path)
        try:
            with open(file_path, "r", encoding=encoding) as f:
                lines = f.readlines()
            file_content = "".join(lines)
            return lines, file_content, len(lines)
        except FileNotFoundError as err:
            raise FileNotFoundError(f"File not found: {file_path}") from err
        except UnicodeDecodeError as err:
            raise UnicodeDecodeError(
                encoding,
                err.object,
                err.start,
                err.end,
                f"Failed to decode file '{file_path}' with {encoding} encoding",
            ) from err

    async def read_multiple_ranges(
        self, ranges: List[Dict[str, Any]], encoding: str = "utf-8"
    ) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}

        for file_range_dict in ranges:
            file_range = FileRanges.model_validate(file_range_dict)
            file_path = file_range.file_path
            lines, file_content, total_lines = await self._read_file(
                file_path, encoding=encoding
            )
            result[file_path] = {"ranges": []}

            for range_spec in file_range.ranges:
                start = max(1, range_spec.start) - 1
                end_value = range_spec.end
                end = (
                    min(total_lines, end_value)
                    if end_value is not None
                    else total_lines
                )

                if start >= total_lines:
                    empty_content = ""
                    result[file_path]["ranges"].append(
                        {
                            "content": empty_content,
                            "start": start + 1,
                            "end": start + 1,
                            "total_lines": total_lines,
                            "content_size": 0,
                        }
                    )
                    continue

                selected_lines = lines[start:end]
                content = "".join(selected_lines)

                result[file_path]["ranges"].append(
                    {
                        "content": content,
                        "start": start + 1,
                        "end": end,
                        "total_lines": total_lines,
                        "content_size": len(content),
                    }
                )

        return result

    async def read_file_contents(
        self,
        file_path: str,
        start: int = 1,
        end: Optional[int] = None,
        encoding: str = "utf-8",
    ) -> Tuple[str, int, int, int, int]:
        lines, file_content, total_lines = await self._read_file(
            file_path, encoding=encoding
        )

        if end is not None and end < start:
            raise ValueError("End line must be greater than or equal to start line")

        start = max(1, start) - 1
        end = total_lines if end is None else min(end, total_lines)

        if start >= total_lines:
            empty_content = ""
            return empty_content, start, start, total_lines, 0
        if end < start:
            raise ValueError("End line must be greater than or equal to start line")

        selected_lines = lines[start:end]
        content = "".join(selected_lines)
        content_size = len(content.encode(encoding))

        return (
            content,
            start + 1,
            end,
            total_lines,
            content_size,
        )


    async def edit_file_contents_v2(
        self,
        file_path: str,
        patches: List[Dict[str, Any]],
        encoding: str = "utf-8",
        require_exact_match: bool = False,
    ) -> Dict[str, Any]:
        """
        Edit file contents with string-based validation and multi-range patches.

        Args:
            file_path (str): Path to the file to edit
            patches (List[Dict[str, Any]]): List of patches to apply, each containing:
                - old_string (str): Expected content to be replaced
                - new_string (str): New content to replace with
                - ranges (List[Dict]): Line ranges where this patch applies
                    - start (int): Starting line number (1-based)
                    - end (Optional[int]): Ending line number (null for end of file)
            encoding (str): File encoding
            require_exact_match (bool): If True, requires exact whitespace matching. 
                                      If False, ignores trailing whitespace per line.

        Returns:
            Dict[str, Any]: Results of the operation containing:
                - result: "ok" or "error"
                - hash: New file hash if successful, None if error
                - reason: Error message if result is "error"
        """
        self._validate_file_path(file_path)
        try:
            if not os.path.exists(file_path):
                return self.create_error_response(
                    f"File not found: {file_path}",
                    hint="File must exist before applying patches",
                )

            # Read current file content
            (
                current_file_content,
                _,
                _,
                total_lines,
                _,
            ) = await self.read_file_contents(file_path, encoding=encoding)

            if not current_file_content:
                current_file_content = ""
                lines = []
            else:
                lines = current_file_content.splitlines(keepends=True)

            # Collect all ranges for overlap validation
            all_ranges = []
            for patch in patches:
                patch_ranges = patch["ranges"]
                
                # Validate ranges within this patch don't overlap
                for i in range(len(patch_ranges)):
                    for j in range(i + 1, len(patch_ranges)):
                        if self._ranges_overlap(patch_ranges[i], patch_ranges[j]):
                            return self.create_error_response(
                                "Overlapping ranges within patch detected",
                                suggestion="patch",
                                hint="Ranges within a single patch cannot overlap",
                            )
                
                # Collect ranges for inter-patch validation
                all_ranges.extend(patch_ranges)

            # Validate ranges across patches don't overlap
            for i in range(len(all_ranges)):
                for j in range(i + 1, len(all_ranges)):
                    if self._ranges_overlap(all_ranges[i], all_ranges[j]):
                        return self.create_error_response(
                            "Overlapping ranges across patches detected",
                            suggestion="patch",
                            hint="Ranges across different patches cannot overlap",
                        )

            # Validate string content and apply patches
            # Process patches in reverse order to avoid line number shifts
            sorted_patches = sorted(
                patches,
                key=lambda patch: max(
                    range_spec["start"] for range_spec in patch["ranges"]
                ),
                reverse=True,
            )

            for patch in sorted_patches:
                old_string = patch["old_string"]
                new_string = patch["new_string"]
                ranges = patch["ranges"]

                # Validate all ranges contain the expected content
                for range_spec in ranges:
                    start_zero = range_spec["start"] - 1
                    end_zero = (
                        len(lines) - 1
                        if range_spec["end"] is None
                        else range_spec["end"] - 1
                    )

                    # Validate range bounds
                    if start_zero < 0 or start_zero >= len(lines):
                        return self.create_error_response(
                            f"Invalid start line {range_spec['start']}: out of range",
                            suggestion="patch",
                            hint="Line numbers must be within file bounds",
                        )

                    if range_spec["end"] is not None and (
                        end_zero < start_zero or end_zero >= len(lines)
                    ):
                        return self.create_error_response(
                            f"Invalid end line {range_spec['end']}: out of range",
                            suggestion="patch",
                            hint="End line must be >= start line and within file bounds",
                        )

                    actual_content = "".join(lines[start_zero : end_zero + 1])
                    if not self._content_matches(actual_content, old_string, require_exact_match):
                        return self.create_error_response(
                            f"Content at lines {range_spec['start']}-{range_spec['end'] or 'EOF'} does not match expected string",
                            suggestion="patch",
                            hint="The old_string must match the content at specified ranges" + (
                                " (exact whitespace match required)" if require_exact_match 
                                else " (trailing whitespace ignored)"
                            ),
                        )

                # Apply replacement to all ranges (in reverse order)
                sorted_ranges = sorted(
                    ranges,
                    key=lambda r: r["start"],
                    reverse=True,
                )

                for range_spec in sorted_ranges:
                    start_zero = range_spec["start"] - 1
                    end_zero = (
                        len(lines) - 1
                        if range_spec["end"] is None
                        else range_spec["end"] - 1
                    )

                    # Replace content
                    new_content = new_string if new_string.endswith("\n") else new_string + "\n"
                    new_lines = new_content.splitlines(keepends=True)
                    lines[start_zero : end_zero + 1] = new_lines

            # Write the final content back to file
            final_content = "".join(lines)
            with open(file_path, "w", encoding=encoding) as f:
                f.write(final_content)

            return {
                "result": "ok",
                "reason": None,
            }

        except FileNotFoundError:
            return self.create_error_response(
                f"File not found: {file_path}",
                hint="File must exist before applying patches",
            )
        except (IOError, UnicodeError, PermissionError) as e:
            return self.create_error_response(
                f"Error editing file: {str(e)}",
                suggestion="patch",
                hint="Please check file permissions and try again",
            )
        except Exception as e:
            import traceback

            logger.error(f"Error: {str(e)}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            return self.create_error_response(
                f"Error: {str(e)}",
                suggestion="patch",
                hint="Please try again or report the issue if it persists",
            )

    def _ranges_overlap(self, range1: Dict[str, Any], range2: Dict[str, Any]) -> bool:
        """Check if two ranges overlap."""
        start1 = range1["start"]
        end1 = range1["end"] or start1
        start2 = range2["start"]
        end2 = range2["end"] or start2

        return start1 <= end2 and end1 >= start2

    def _content_matches(self, actual: str, expected: str, require_exact_match: bool = False) -> bool:
        """
        Compare two strings with optional whitespace flexibility.
        
        Args:
            actual: Actual content from file
            expected: Expected content to match
            require_exact_match: If True, requires exact match. If False, ignores trailing whitespace per line.
            
        Returns:
            bool: True if content matches according to the matching rules
        """
        if require_exact_match:
            return actual == expected
            
        # For flexible matching, compare line by line ignoring trailing whitespace
        actual_lines = actual.splitlines()
        expected_lines = expected.splitlines()
        
        # Must have same number of lines
        if len(actual_lines) != len(expected_lines):
            return False
            
        # Compare each line ignoring trailing whitespace
        for actual_line, expected_line in zip(actual_lines, expected_lines):
            if actual_line.rstrip() != expected_line.rstrip():
                return False
                
        return True



    async def delete_text_file_contents_v2(
        self,
        file_path: str,
        deletions: List[Dict[str, Any]],
        encoding: str = "utf-8",
        require_exact_match: bool = False,
    ) -> Dict[str, Any]:
        """
        Delete file contents with string-based validation and multi-range deletions.

        Args:
            file_path (str): Path to the file to edit
            deletions (List[Dict[str, Any]]): List of deletion operations, each containing:
                - expected_content (str): Expected content to be deleted
                - ranges (List[Dict]): Line ranges where this content should be deleted
                    - start (int): Starting line number (1-based)
                    - end (Optional[int]): Ending line number (null for end of file)
            encoding (str): File encoding
            require_exact_match (bool): If True, requires exact whitespace matching. 
                                      If False, ignores trailing whitespace per line.

        Returns:
            Dict[str, Any]: Results of the operation
        """
        self._validate_file_path(file_path)
        try:
            if not os.path.exists(file_path):
                return self.create_error_response(
                    f"File not found: {file_path}",
                    hint="File must exist before deleting content",
                )

            # Read current file content
            (
                current_file_content,
                _,
                _,
                total_lines,
                _,
            ) = await self.read_file_contents(file_path, encoding=encoding)

            if not current_file_content:
                lines = []
            else:
                lines = current_file_content.splitlines(keepends=True)

            # Collect all ranges for overlap validation
            all_ranges = []
            for deletion in deletions:
                deletion_ranges = deletion["ranges"]
                
                # Validate ranges within this deletion don't overlap
                for i in range(len(deletion_ranges)):
                    for j in range(i + 1, len(deletion_ranges)):
                        if self._ranges_overlap(deletion_ranges[i], deletion_ranges[j]):
                            return self.create_error_response(
                                "Overlapping ranges within deletion detected",
                                hint="Ranges within a single deletion cannot overlap",
                            )
                
                all_ranges.extend(deletion_ranges)

            # Validate ranges across deletions don't overlap
            for i in range(len(all_ranges)):
                for j in range(i + 1, len(all_ranges)):
                    if self._ranges_overlap(all_ranges[i], all_ranges[j]):
                        return self.create_error_response(
                            "Overlapping ranges across deletions detected",
                            hint="Ranges across different deletions cannot overlap",
                        )

            # Validate string content and apply deletions
            # Process deletions in reverse order to avoid line number shifts
            sorted_deletions = sorted(
                deletions,
                key=lambda deletion: max(
                    range_spec["start"] for range_spec in deletion["ranges"]
                ),
                reverse=True,
            )

            for deletion in sorted_deletions:
                expected_content = deletion["expected_content"]
                ranges = deletion["ranges"]

                # Validate all ranges contain the expected content
                for range_spec in ranges:
                    start_zero = range_spec["start"] - 1
                    end_zero = (
                        len(lines) - 1
                        if range_spec["end"] is None
                        else range_spec["end"] - 1
                    )

                    if start_zero < 0 or start_zero >= len(lines):
                        return self.create_error_response(
                            f"Start line {range_spec['start']} is out of range (file has {len(lines)} lines)",
                        )

                    if end_zero >= len(lines):
                        return self.create_error_response(
                            f"End line {range_spec['end']} is out of range (file has {len(lines)} lines)",
                        )

                    actual_content = "".join(lines[start_zero:end_zero + 1])
                    if not self._content_matches(actual_content, expected_content, require_exact_match):
                        return self.create_error_response(
                            f"Content at lines {range_spec['start']}-{range_spec['end'] or 'end'} does not match expected string",
                            hint="Check that the expected content matches the file content" + (
                                " (exact whitespace match required)" if require_exact_match 
                                else " (trailing whitespace ignored)"
                            ),
                        )

                # Apply deletion to all ranges (process in reverse order)
                for range_spec in sorted(ranges, key=lambda r: r["start"], reverse=True):
                    start_zero = range_spec["start"] - 1
                    end_zero = (
                        len(lines) - 1
                        if range_spec["end"] is None
                        else range_spec["end"] - 1
                    )
                    
                    # Delete the range
                    del lines[start_zero:end_zero + 1]

            # Write the modified content
            new_content = "".join(lines)
            with open(file_path, "w", encoding=encoding) as f:
                f.write(new_content)

            return {
                "result": "ok",
            }

        except Exception as e:
            logger.error(f"Error in delete_text_file_contents_v2: {str(e)}")
            return self.create_error_response(str(e))

    async def insert_text_file_contents_v2(
        self,
        file_path: str,
        insertions: List[Dict[str, Any]],
        encoding: str = "utf-8",
        require_exact_match: bool = False,
    ) -> Dict[str, Any]:
        """
        Insert content into file with context validation.

        Args:
            file_path (str): Path to the file to edit
            insertions (List[Dict[str, Any]]): List of insertion operations, each containing:
                - content_to_insert (str): Content to insert
                - position (str): "before" or "after" the reference line
                - context_line (str): Expected content of the reference line
                - line_number (int): Line number of the reference line
            encoding (str): File encoding
            require_exact_match (bool): If True, requires exact whitespace matching. 
                                      If False, ignores trailing whitespace per line.

        Returns:
            Dict[str, Any]: Results of the operation
        """
        self._validate_file_path(file_path)
        try:
            if not os.path.exists(file_path):
                return self.create_error_response(
                    f"File not found: {file_path}",
                    hint="File must exist before inserting content",
                )

            # Read current file content
            (
                current_file_content,
                _,
                _,
                total_lines,
                _,
            ) = await self.read_file_contents(file_path, encoding=encoding)

            if not current_file_content:
                lines = []
            else:
                lines = current_file_content.splitlines(keepends=True)

            # Validate and apply insertions
            # Process insertions in reverse order to avoid line number shifts
            sorted_insertions = sorted(
                insertions,
                key=lambda insertion: insertion["line_number"],
                reverse=True,
            )

            for insertion in sorted_insertions:
                content_to_insert = insertion["content_to_insert"]
                position = insertion["position"]
                context_line = insertion["context_line"]
                line_number = insertion["line_number"]

                # Validate line number
                if line_number < 1 or line_number > len(lines):
                    return self.create_error_response(
                        f"Line number {line_number} is out of range (file has {len(lines)} lines)",
                    )

                # Validate context line
                actual_line_content = lines[line_number - 1]
                if not self._content_matches(actual_line_content, context_line + '\n', require_exact_match):
                    return self.create_error_response(
                        f"Content at line {line_number} does not match expected context",
                        hint="Check that the context line matches the file content" + (
                            " (exact whitespace match required)" if require_exact_match 
                            else " (trailing whitespace ignored)"
                        ),
                    )

                # Ensure content to insert ends with newline if it doesn't already
                if not content_to_insert.endswith('\n'):
                    content_to_insert += '\n'

                # Insert content
                if position == "before":
                    lines.insert(line_number - 1, content_to_insert)
                else:  # position == "after"
                    lines.insert(line_number, content_to_insert)

            # Write the modified content
            new_content = "".join(lines)
            with open(file_path, "w", encoding=encoding) as f:
                f.write(new_content)

            return {
                "result": "ok",
            }

        except Exception as e:
            logger.error(f"Error in insert_text_file_contents_v2: {str(e)}")
            return self.create_error_response(str(e))

    async def append_text_file_contents_v2(
        self,
        file_path: str,
        content_to_append: str,
        expected_file_ending: str,
        encoding: str = "utf-8",
        require_exact_match: bool = False,
    ) -> Dict[str, Any]:
        """
        Append content to file with final-line validation.

        Args:
            file_path (str): Path to the file to edit
            content_to_append (str): Content to append to the file
            expected_file_ending (str): Expected content of the final line for validation
            encoding (str): Text encoding
            require_exact_match (bool): If True, requires exact whitespace matching. 
                                      If False, ignores trailing whitespace per line.

        Returns:
            Dict[str, Any]: Results of the operation
        """
        self._validate_file_path(file_path)
        try:
            if not os.path.exists(file_path):
                return self.create_error_response(
                    f"File not found: {file_path}",
                    hint="File must exist before appending content",
                )

            # Read current file content
            (
                current_file_content,
                _,
                _,
                total_lines,
                _,
            ) = await self.read_file_contents(file_path, encoding=encoding)

            if not current_file_content:
                lines = []
            else:
                lines = current_file_content.splitlines(keepends=True)

            # Validate final line if file is not empty
            if lines:
                actual_final_line_content = lines[-1]
                expected_final_line_content = expected_file_ending + '\n' if not expected_file_ending.endswith('\n') else expected_file_ending
                
                if not self._content_matches(actual_final_line_content, expected_final_line_content, require_exact_match):
                    return self.create_error_response(
                        "Final line does not match expected content",
                        hint="Check that the expected file ending matches the final line" + (
                            " (exact whitespace match required)" if require_exact_match 
                            else " (trailing whitespace ignored)"
                        ),
                    )

            # Ensure content to append ends with newline if it doesn't already
            if not content_to_append.endswith('\n'):
                content_to_append += '\n'

            # Append content
            with open(file_path, "a", encoding=encoding) as f:
                f.write(content_to_append)

            return {
                "result": "ok",
            }

        except Exception as e:
            logger.error(f"Error in append_text_file_contents_v2: {str(e)}")
            return self.create_error_response(str(e))
