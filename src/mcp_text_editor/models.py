"""Data models for the MCP Text Editor Server."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class GetTextFileContentsRequest(BaseModel):
    """Request model for getting text file contents."""

    file_path: str = Field(..., description="Path to the text file")
    start: int = Field(1, description="Starting line number (1-based)")
    end: Optional[int] = Field(None, description="Ending line number (inclusive)")


class GetTextFileContentsResponse(BaseModel):
    """Response model for getting text file contents."""

    contents: str = Field(..., description="File contents")
    start: int = Field(..., description="Starting line number")
    end: int = Field(..., description="Ending line number")
    hash: str = Field(..., description="Hash of the contents")


class EditPatch(BaseModel):
    """Model for a single edit patch operation."""

    start: int = Field(1, description="Starting line for edit")
    end: Optional[int] = Field(None, description="Ending line for edit")
    contents: str = Field(..., description="New content to insert")
    range_hash: Optional[str] = Field(
        None,  # None for new patches, must be explicitly set
        description="Hash of content being replaced. Empty string for insertions.",
    )

    @model_validator(mode="after")
    def validate_range_hash(self) -> "EditPatch":
        """Validate that range_hash is set and handle end field validation."""
        # range_hash must be explicitly set
        if self.range_hash is None:
            raise ValueError("range_hash is required")

        # For safety, convert None to the special range hash value
        if self.end is None and self.range_hash != "":
            # Special case: patch with end=None is allowed
            pass

        return self


class EditFileOperation(BaseModel):
    """Model for individual file edit operation."""

    path: str = Field(..., description="Path to the file")
    hash: str = Field(..., description="Hash of original contents")
    patches: List[EditPatch] = Field(..., description="Edit operations to apply")


class EditResult(BaseModel):
    """Model for edit operation result."""

    result: str = Field(..., description="Operation result (ok/error)")
    reason: Optional[str] = Field(None, description="Error message if applicable")
    hash: Optional[str] = Field(
        None, description="Current content hash (None for missing files)"
    )

    @model_validator(mode="after")
    def validate_error_result(self) -> "EditResult":
        """Remove hash when result is error."""
        if self.result == "error":
            object.__setattr__(self, "hash", None)
        return self

    def to_dict(self) -> Dict:
        """Convert EditResult to a dictionary."""
        result = {"result": self.result}
        if self.reason is not None:
            result["reason"] = self.reason
        if self.hash is not None:
            result["hash"] = self.hash
        return result


class EditTextFileContentsRequest(BaseModel):
    """Request model for editing text file contents.

    Example:
    {
        "files": [
            {
                "path": "/path/to/file",
                "hash": "abc123...",
                "patches": [
                    {
                        "start": 1,  # default: 1 (top of file)
                        "end": null,  # default: null (end of file)
                        "contents": "new content"
                    }
                ]
            }
        ]
    }
    """

    files: List[EditFileOperation] = Field(..., description="List of file operations")


class FileRange(BaseModel):
    """Represents a line range in a file."""

    start: int = Field(..., description="Starting line number (1-based)")
    end: Optional[int] = Field(
        None, description="Ending line number (null for end of file)"
    )
    range_hash: Optional[str] = Field(
        None, description="Hash of the content to be deleted"
    )


class FileRanges(BaseModel):
    """Represents a file and its line ranges."""

    file_path: str = Field(..., description="Path to the text file")
    ranges: List[FileRange] = Field(
        ..., description="List of line ranges to read from the file"
    )





class PatchTextFileContentsRequest(BaseModel):
    """Request model for patching text in a file.
    Example:
    {
        "file_path": "/path/to/file",
        "file_hash": "abc123...",
        "patches": [
            {
                "start": 5,
                "end": 10,
                "contents": "new content",
                "range_hash": "def456..."
            }
        ]
    }
    """

    file_path: str = Field(..., description="Path to the text file")
    file_hash: str = Field(..., description="Hash of original contents")
    patches: List[EditPatch] = Field(..., description="List of patches to apply")
    encoding: Optional[str] = Field(
        "utf-8", description="Text encoding (default: 'utf-8')"
    )


class PatchRange(BaseModel):
    """Represents a line range for patching."""
    start: int = Field(..., description="Starting line number (1-based)")
    end: Optional[int] = Field(None, description="Ending line number (null for end of file)")


class StringPatch(BaseModel):
    """Model for string-based patch operation."""
    old_string: str = Field(..., description="Expected content to be replaced")
    new_string: str = Field(..., description="New content to replace with")
    ranges: List[PatchRange] = Field(..., description="Line ranges where this patch applies")


class FileOperation(BaseModel):
    """Model for file operation in new API."""
    file_path: str = Field(..., description="Path to the file")
    encoding: Optional[str] = Field("utf-8", description="Text encoding")
    patches: List[StringPatch] = Field(..., description="Patches to apply")


class NewPatchTextFileContentsRequest(BaseModel):
    """New request model for patching text files."""
    files: List[FileOperation] = Field(..., description="List of file operations")


# New string-based models for delete, insert, append operations

class DeleteOperation(BaseModel):
    """Model for string-based delete operation."""
    expected_content: str = Field(..., description="Expected content to be deleted")
    ranges: List[PatchRange] = Field(..., description="Line ranges where this content should be deleted")


class DeleteTextFileContentsRequestV2(BaseModel):
    """New request model for deleting text from files using string validation."""
    file_path: str = Field(..., description="Path to the text file")
    deletions: List[DeleteOperation] = Field(..., min_length=1, description="List of deletion operations")
    encoding: Optional[str] = Field("utf-8", description="Text encoding")


class InsertOperation(BaseModel):
    """Model for string-based insert operation."""
    content_to_insert: str = Field(..., description="Content to insert")
    position: str = Field(..., description="Position relative to reference line ('before' or 'after')")
    context_line: str = Field(..., description="Expected content of the reference line")
    line_number: int = Field(..., description="Line number of the reference line")
    
    @field_validator("position")
    def validate_position(cls, v):
        if v not in ["before", "after"]:
            raise ValueError("Position must be 'before' or 'after'")
        return v
    
    @field_validator("line_number")
    def validate_line_number(cls, v):
        if v < 1:
            raise ValueError("Line number must be positive")
        return v


class InsertTextFileContentsRequestV2(BaseModel):
    """New request model for inserting text using context validation."""
    file_path: str = Field(..., description="Path to the text file")
    insertions: List[InsertOperation] = Field(..., description="List of insertion operations")
    encoding: Optional[str] = Field("utf-8", description="Text encoding")


class AppendTextFileContentsRequestV2(BaseModel):
    """New request model for appending text using final-line validation."""
    file_path: str = Field(..., description="Path to the text file")
    content_to_append: str = Field(..., description="Content to append to the file")
    expected_file_ending: str = Field(..., description="Expected content of the final line for validation")
    encoding: Optional[str] = Field("utf-8", description="Text encoding")
