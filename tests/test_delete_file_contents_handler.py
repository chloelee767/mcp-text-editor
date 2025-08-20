"""Tests for delete_text_file_contents functionality with new string-based API."""

import json

import pytest

from mcp_text_editor.handlers.delete_text_file_contents import DeleteTextFileContentsHandler
from mcp_text_editor.text_editor import TextEditor


@pytest.fixture
def editor():
    """Create TextEditor instance."""
    return TextEditor()

@pytest.fixture
def handler(editor):
    """Create DeleteTextFileContentsHandler instance."""
    return DeleteTextFileContentsHandler(editor)


@pytest.mark.asyncio
async def test_delete_text_file_contents_basic(handler, tmp_path):
    """Test basic delete operation."""
    # Create test file
    test_file = tmp_path / "delete_test.txt"
    test_content = "line1\nline2\nline3\n"
    test_file.write_text(test_content)
    file_path = str(test_file)

    # Create delete request with new format
    arguments = {
        "file_path": file_path,
        "deletions": [
            {
                "expected_content": "line2\n",
                "ranges": [{"start": 2, "end": 2}]
            }
        ],
        "encoding": "utf-8",
    }

    # Apply delete
    result = await handler.run_tool(arguments)
    assert len(result) == 1
    response = json.loads(result[0].text)
    assert response["result"] == "ok"

    # Verify changes
    new_content = test_file.read_text()
    assert new_content == "line1\nline3\n"


@pytest.mark.asyncio
async def test_delete_text_file_contents_string_mismatch(handler, tmp_path):
    """Test deleting with string content mismatch."""
    # Create test file
    test_file = tmp_path / "string_mismatch_test.txt"
    test_content = "line1\nline2\nline3\n"
    test_file.write_text(test_content)
    file_path = str(test_file)

    # Create delete request with incorrect expected content
    arguments = {
        "file_path": file_path,
        "deletions": [
            {
                "expected_content": "wrong_content\n",  # This doesn't match actual line2
                "ranges": [{"start": 2, "end": 2}]
            }
        ],
        "encoding": "utf-8",
    }

    # Attempt delete
    result = await handler.run_tool(arguments)
    assert len(result) == 1
    response = json.loads(result[0].text)
    assert response["result"] == "error"
    assert "does not match expected" in response["reason"].lower() or "content mismatch" in response["reason"].lower()


@pytest.mark.asyncio
async def test_delete_text_file_contents_invalid_ranges(handler, tmp_path):
    """Test deleting with invalid ranges."""
    # Create test file
    test_file = tmp_path / "invalid_ranges_test.txt"
    test_content = "line1\nline2\nline3\n"
    test_file.write_text(test_content)
    file_path = str(test_file)

    # Create delete request with invalid ranges
    arguments = {
        "file_path": file_path,
        "deletions": [
            {
                "expected_content": "some_content\n",
                "ranges": [{"start": 1, "end": 10}]  # Beyond file length
            }
        ],
        "encoding": "utf-8",
    }

    # Attempt delete
    result = await handler.run_tool(arguments)
    assert len(result) == 1
    response = json.loads(result[0].text)
    assert response["result"] == "error"
    assert "range" in response["reason"].lower() or "line" in response["reason"].lower()


@pytest.mark.asyncio
async def test_delete_text_file_contents_multiple_ranges(handler, tmp_path):
    """Test deleting multiple ranges in one operation."""
    # Create test file
    test_file = tmp_path / "multiple_ranges_test.txt"
    test_content = "line1\nline2\nline3\nline4\nline5\n"
    test_file.write_text(test_content)
    file_path = str(test_file)

    # Create delete request with multiple deletion operations
    arguments = {
        "file_path": file_path,
        "deletions": [
            {
                "expected_content": "line2\n",
                "ranges": [{"start": 2, "end": 2}]
            },
            {
                "expected_content": "line4\n",
                "ranges": [{"start": 4, "end": 4}]
            }
        ],
        "encoding": "utf-8",
    }

    # Apply delete
    result = await handler.run_tool(arguments)
    assert len(result) == 1
    response = json.loads(result[0].text)
    assert response["result"] == "ok"

    # Verify changes
    new_content = test_file.read_text()
    assert new_content == "line1\nline3\nline5\n"


@pytest.mark.asyncio
async def test_delete_text_file_contents_nonexistent_file(handler, tmp_path):
    """Test deleting content from a nonexistent file."""
    file_path = str(tmp_path / "nonexistent.txt")

    # Create delete request for nonexistent file
    arguments = {
        "file_path": file_path,
        "deletions": [
            {
                "expected_content": "some_content\n",
                "ranges": [{"start": 1, "end": 1}]
            }
        ],
        "encoding": "utf-8",
    }

    # Attempt delete - should fail at handler level
    with pytest.raises(RuntimeError) as exc_info:
        await handler.run_tool(arguments)
    assert "File does not exist" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_text_file_contents_handler_validation():
    """Test validation in DeleteTextFileContentsHandler."""
    from mcp_text_editor.handlers.delete_text_file_contents import (
        DeleteTextFileContentsHandler,
    )
    from mcp_text_editor.text_editor import TextEditor

    editor = TextEditor()
    handler = DeleteTextFileContentsHandler(editor)

    # Test missing deletions
    with pytest.raises(RuntimeError) as exc_info:
        arguments = {
            "file_path": "/absolute/path.txt",
            "encoding": "utf-8",
        }
        await handler.run_tool(arguments)
    assert ("deletions" in str(exc_info.value) and "required" in str(exc_info.value).lower()) or "Field required" in str(exc_info.value)

    # Test missing file_path
    with pytest.raises(RuntimeError) as exc_info:
        arguments = {
            "deletions": [{"expected_content": "content", "ranges": [{"start": 1}]}],
            "encoding": "utf-8",
        }
        await handler.run_tool(arguments)
    assert ("file_path" in str(exc_info.value) and "required" in str(exc_info.value).lower()) or "Field required" in str(exc_info.value)

    # Test relative file path
    with pytest.raises(RuntimeError) as exc_info:
        arguments = {
            "file_path": "relative/path.txt",
            "deletions": [{"expected_content": "content", "ranges": [{"start": 1}]}],
            "encoding": "utf-8",
        }
        await handler.run_tool(arguments)
    assert "File path must be absolute" in str(exc_info.value)
    
    # Test empty deletions list
    with pytest.raises(RuntimeError) as exc_info:
        arguments = {
            "file_path": "/absolute/path.txt",
            "deletions": [],
            "encoding": "utf-8",
        }
        await handler.run_tool(arguments)
    assert "List should have at least 1 item" in str(exc_info.value) or "list should have at least 1 item" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_text_file_contents_multi_range_same_content(handler, tmp_path):
    """Test deleting same content from multiple ranges."""
    # Create test file with repeated content
    test_file = tmp_path / "multi_range_test.txt"
    test_content = "line1\nDUPLICATE\nline3\nDUPLICATE\nline5\n"
    test_file.write_text(test_content)
    file_path = str(test_file)

    # Delete the same content from multiple locations
    arguments = {
        "file_path": file_path,
        "deletions": [
            {
                "expected_content": "DUPLICATE\n",
                "ranges": [
                    {"start": 2, "end": 2},
                    {"start": 4, "end": 4}
                ]
            }
        ],
        "encoding": "utf-8",
    }

    # Apply delete
    result = await handler.run_tool(arguments)
    assert len(result) == 1
    response = json.loads(result[0].text)
    assert response["result"] == "ok"

    # Verify changes
    new_content = test_file.read_text()
    assert new_content == "line1\nline3\nline5\n"
