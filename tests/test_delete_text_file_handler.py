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


@pytest.mark.asyncio
async def test_delete_require_exact_match_multi_line_whitespace(editor, tmp_path):
    """Test require_exact_match with multi-line deletions having varying whitespace."""
    test_file = tmp_path / "multiline_delete.txt"
    # Create content with trailing whitespace
    content = "Line 1   \nLine 2\nLine 3\t\n"
    test_file.write_text(content)
    
    # Test flexible matching (default) - should succeed ignoring whitespace
    deletions = [
        {
            "expected_content": "Line 1\nLine 2",
            "ranges": [{"start": 1, "end": 2}]
        }
    ]
    
    result = await editor.delete_text_file_contents_v2(
        file_path=str(test_file),
        deletions=deletions,
    )
    assert result["result"] == "ok"
    
    # Reset file
    test_file.write_text(content)
    
    # Test exact matching - should fail with mismatched whitespace
    result = await editor.delete_text_file_contents_v2(
        file_path=str(test_file),
        deletions=deletions,
        require_exact_match=True
    )
    assert result["result"] == "error"
    assert "exact whitespace match required" in result["hint"]
    
    # Test exact matching with correct whitespace - should succeed
    deletions_exact = [
        {
            "expected_content": "Line 1   \nLine 2\n",
            "ranges": [{"start": 1, "end": 2}]
        }
    ]
    
    result = await editor.delete_text_file_contents_v2(
        file_path=str(test_file),
        deletions=deletions_exact,
        require_exact_match=True
    )
    assert result["result"] == "ok"
    assert test_file.read_text() == "Line 3\t\n"


@pytest.mark.asyncio
async def test_delete_whitespace_only_lines(editor, tmp_path):
    """Test deleting lines containing only whitespace."""
    test_file = tmp_path / "whitespace_lines.txt"
    content = "Line 1\n   \n\t\t\n  \nLine 5\n"
    test_file.write_text(content)
    
    # Test flexible deletion of whitespace-only lines (lines 2-4 contain whitespace)
    deletions = [
        {
            "expected_content": "\n\n\n",  # 3 lines with flexible whitespace matching
            "ranges": [{"start": 2, "end": 4}]
        }
    ]
    
    result = await editor.delete_text_file_contents_v2(
        file_path=str(test_file),
        deletions=deletions,
    )
    assert result["result"] == "ok"
    assert test_file.read_text() == "Line 1\nLine 5\n"
    
    # Reset and test exact matching
    test_file.write_text(content)
    
    # Exact matching should fail with whitespace-only line differences
    result = await editor.delete_text_file_contents_v2(
        file_path=str(test_file),
        deletions=deletions,
        require_exact_match=True
    )
    assert result["result"] == "error"
    assert "exact whitespace match required" in result["hint"]
    
    # Test exact matching with correct whitespace content
    deletions_exact = [
        {
            "expected_content": "   \n\t\t\n  \n",
            "ranges": [{"start": 2, "end": 4}]
        }
    ]
    
    result = await editor.delete_text_file_contents_v2(
        file_path=str(test_file),
        deletions=deletions_exact,
        require_exact_match=True
    )
    assert result["result"] == "ok"
    assert test_file.read_text() == "Line 1\nLine 5\n"


@pytest.mark.asyncio
async def test_delete_mixed_whitespace_types(editor, tmp_path):
    """Test deletion with mixed spaces and tabs."""
    test_file = tmp_path / "mixed_whitespace_delete.txt"
    content = "\tTab line\n    Space line\n\t  Mixed line\n"
    test_file.write_text(content)
    
    # Flexible matching should work ignoring leading/trailing whitespace
    deletions = [
        {
            "expected_content": "Tab line\nSpace line",
            "ranges": [{"start": 1, "end": 2}]
        }
    ]
    
    result = await editor.delete_text_file_contents_v2(
        file_path=str(test_file),
        deletions=deletions,
    )
    assert result["result"] == "ok"
    
    # Reset and test exact matching
    test_file.write_text(content)
    
    result = await editor.delete_text_file_contents_v2(
        file_path=str(test_file),
        deletions=deletions,
        require_exact_match=True
    )
    assert result["result"] == "error"
    assert "exact whitespace match required" in result["hint"]
