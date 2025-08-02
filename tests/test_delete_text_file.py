"""Tests for delete text file functionality using new string-based API."""

from pathlib import Path

import pytest

from mcp_text_editor.text_editor import TextEditor


@pytest.fixture
def editor() -> TextEditor:
    """Create TextEditor instance."""
    return TextEditor()


@pytest.fixture
def test_file(tmp_path) -> Path:
    """Create a test file with sample content."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")
    return test_file


@pytest.mark.asyncio
async def test_delete_single_line(editor, test_file):
    """Test deleting a single line from file using V2 API."""
    # Delete line 2 using the new string-based API
    deletions = [
        {
            "expected_content": "Line 2\n",
            "ranges": [{"start": 2, "end": 2}]
        }
    ]

    result = await editor.delete_text_file_contents_v2(
        file_path=str(test_file),
        deletions=deletions,
    )

    assert result["result"] == "ok"
    assert test_file.read_text() == "Line 1\nLine 3\nLine 4\nLine 5\n"


@pytest.mark.asyncio
async def test_delete_multiple_lines(editor, test_file):
    """Test deleting multiple consecutive lines from file using V2 API."""
    # Delete lines 2-4 using the new string-based API
    deletions = [
        {
            "expected_content": "Line 2\nLine 3\nLine 4\n",
            "ranges": [{"start": 2, "end": 4}]
        }
    ]

    result = await editor.delete_text_file_contents_v2(
        file_path=str(test_file),
        deletions=deletions,
    )

    assert result["result"] == "ok"
    assert test_file.read_text() == "Line 1\nLine 5\n"


@pytest.mark.asyncio
async def test_delete_with_content_mismatch(editor, test_file):
    """Test deleting with content that doesn't match."""
    # Try to delete content that doesn't match what's actually on line 2
    deletions = [
        {
            "expected_content": "Wrong Content\n",  # This doesn't match "Line 2\n"
            "ranges": [{"start": 2, "end": 2}]
        }
    ]

    result = await editor.delete_text_file_contents_v2(
        file_path=str(test_file),
        deletions=deletions,
    )

    assert result["result"] == "error"
    assert "does not match expected" in result["reason"].lower() or "content mismatch" in result["reason"].lower()
    assert test_file.read_text() == "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"


@pytest.mark.asyncio
async def test_delete_with_invalid_range(editor, test_file):
    """Test deleting with invalid line range."""
    # Try to delete with end before start
    deletions = [
        {
            "expected_content": "Line 2\n",
            "ranges": [{"start": 2, "end": 1}]  # Invalid: end before start
        }
    ]

    result = await editor.delete_text_file_contents_v2(
        file_path=str(test_file),
        deletions=deletions,
    )

    assert result["result"] == "error"
    assert "does not match expected" in result["reason"].lower() or "range" in result["reason"].lower() or "invalid" in result["reason"].lower()
    assert test_file.read_text() == "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"


@pytest.mark.asyncio
async def test_delete_multiple_ranges_v2(editor, test_file):
    """Test deleting multiple non-consecutive ranges using V2 API."""
    # Delete lines 2 and 4 in one operation
    deletions = [
        {
            "expected_content": "Line 2\n",
            "ranges": [{"start": 2, "end": 2}]
        },
        {
            "expected_content": "Line 4\n",
            "ranges": [{"start": 4, "end": 4}]
        }
    ]

    result = await editor.delete_text_file_contents_v2(
        file_path=str(test_file),
        deletions=deletions,
    )

    assert result["result"] == "ok"
    assert test_file.read_text() == "Line 1\nLine 3\nLine 5\n"
