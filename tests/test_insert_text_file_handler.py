"""Tests for InsertTextFileContentsHandler."""

import json

import pytest

from mcp_text_editor.handlers.insert_text_file_contents import (
    InsertTextFileContentsHandler,
)
from mcp_text_editor.text_editor import TextEditor


@pytest.fixture
def handler():
    """Create handler instance."""
    editor = TextEditor()
    return InsertTextFileContentsHandler(editor)


@pytest.mark.asyncio
async def test_missing_path(handler):
    """Test handling of missing file_path argument."""
    with pytest.raises(RuntimeError, match="Missing required argument: file_path"):
        await handler.run_tool({"insertions": [{"content_to_insert": "content", "position": "after", "context_line": "line", "line_number": 1}]})


@pytest.mark.asyncio
async def test_missing_insertions(handler):
    """Test handling of missing insertions argument."""
    with pytest.raises(RuntimeError, match="Missing required argument: insertions"):
        await handler.run_tool({"file_path": "/tmp/test.txt"})


@pytest.mark.asyncio
async def test_empty_insertions(handler):
    """Test handling of empty insertions list."""
    with pytest.raises(RuntimeError, match="insertions must be a non-empty list"):
        await handler.run_tool({"file_path": "/tmp/test.txt", "insertions": []})


@pytest.mark.asyncio
async def test_relative_path(handler):
    """Test handling of relative file path."""
    with pytest.raises(RuntimeError, match="File path must be absolute"):
        await handler.run_tool(
            {
                "file_path": "relative/path.txt",
                "insertions": [{"content_to_insert": "content", "position": "before", "context_line": "line", "line_number": 1}],
            }
        )


@pytest.mark.asyncio
async def test_invalid_position(handler, tmp_path):
    """Test handling of invalid position."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("line1\n")
    
    with pytest.raises(RuntimeError, match="position must be 'before' or 'after'"):
        await handler.run_tool(
            {
                "file_path": str(test_file),
                "insertions": [{"content_to_insert": "content", "position": "invalid", "context_line": "line", "line_number": 1}],
            }
        )


@pytest.mark.asyncio
async def test_invalid_line_number(handler, tmp_path):
    """Test handling of invalid line number."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("line1\n")
    
    with pytest.raises(RuntimeError, match="line_number must be a positive integer"):
        await handler.run_tool(
            {
                "file_path": str(test_file),
                "insertions": [{"content_to_insert": "content", "position": "before", "context_line": "line", "line_number": 0}],
            }
        )


@pytest.mark.asyncio
async def test_successful_insert_before(handler, tmp_path):
    """Test successful insert before line."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("line1\nline2\n")

    file_path = str(test_file)

    result = await handler.run_tool(
        {
            "file_path": file_path,
            "insertions": [
                {
                    "content_to_insert": "new_line\n",
                    "position": "before",
                    "context_line": "line2",
                    "line_number": 2,
                }
            ],
        }
    )

    assert len(result) == 1
    assert result[0].type == "text"
    response_data = json.loads(result[0].text)
    assert response_data["result"] == "ok"

    # Verify the content
    assert test_file.read_text() == "line1\nnew_line\nline2\n"


@pytest.mark.asyncio
async def test_successful_insert_after(handler, tmp_path):
    """Test successful insert after line."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("line1\nline2\n")

    file_path = str(test_file)

    result = await handler.run_tool(
        {
            "file_path": file_path,
            "insertions": [
                {
                    "content_to_insert": "new_line\n",
                    "position": "after",
                    "context_line": "line1",
                    "line_number": 1,
                }
            ],
        }
    )

    assert len(result) == 1
    assert result[0].type == "text"
    response_data = json.loads(result[0].text)
    assert response_data["result"] == "ok"

    # Verify the content
    assert test_file.read_text() == "line1\nnew_line\nline2\n"


@pytest.mark.asyncio
async def test_context_validation_failure(handler, tmp_path):
    """Test that context validation prevents incorrect insertions."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("line1\nline2\n")

    file_path = str(test_file)

    result = await handler.run_tool(
        {
            "file_path": file_path,
            "insertions": [
                {
                    "content_to_insert": "new_line\n",
                    "position": "after",
                    "context_line": "wrong_line",  # This doesn't match actual content
                    "line_number": 1,
                }
            ],
        }
    )

    assert len(result) == 1
    assert result[0].type == "text"
    response_data = json.loads(result[0].text)
    assert response_data["result"] == "error"
    assert "does not match expected context" in response_data["reason"]

    # Verify the content is unchanged
    assert test_file.read_text() == "line1\nline2\n"


@pytest.mark.asyncio
async def test_batch_insertions(handler, tmp_path):
    """Test multiple insertions in a single request."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("line1\nline2\nline3\n")

    file_path = str(test_file)

    result = await handler.run_tool(
        {
            "file_path": file_path,
            "insertions": [
                {
                    "content_to_insert": "after_line1\n",
                    "position": "after",
                    "context_line": "line1",
                    "line_number": 1,
                },
                {
                    "content_to_insert": "before_line3\n",
                    "position": "before",
                    "context_line": "line3",
                    "line_number": 3,
                },
            ],
        }
    )

    assert len(result) == 1
    assert result[0].type == "text"
    response_data = json.loads(result[0].text)
    assert response_data["result"] == "ok"

    # Verify the content - note: insertions are processed in reverse line order
    # so line numbers remain valid during processing
    expected_content = "line1\nafter_line1\nline2\nbefore_line3\nline3\n"
    assert test_file.read_text() == expected_content


@pytest.mark.asyncio
async def test_missing_insertion_fields(handler, tmp_path):
    """Test that missing fields in insertion objects are caught."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("line1\nline2\n")

    file_path = str(test_file)

    # Test missing content_to_insert
    with pytest.raises(RuntimeError, match="missing required field: content_to_insert"):
        await handler.run_tool(
            {
                "file_path": file_path,
                "insertions": [
                    {
                        "position": "after",
                        "context_line": "line1",
                        "line_number": 1,
                    }
                ],
            }
        )

    # Test missing position
    with pytest.raises(RuntimeError, match="missing required field: position"):
        await handler.run_tool(
            {
                "file_path": file_path,
                "insertions": [
                    {
                        "content_to_insert": "new_line",
                        "context_line": "line1",
                        "line_number": 1,
                    }
                ],
            }
        )

    # Test missing context_line
    with pytest.raises(RuntimeError, match="missing required field: context_line"):
        await handler.run_tool(
            {
                "file_path": file_path,
                "insertions": [
                    {
                        "content_to_insert": "new_line",
                        "position": "after",
                        "line_number": 1,
                    }
                ],
            }
        )

    # Test missing line_number
    with pytest.raises(RuntimeError, match="missing required field: line_number"):
        await handler.run_tool(
            {
                "file_path": file_path,
                "insertions": [
                    {
                        "content_to_insert": "new_line",
                        "position": "after",
                        "context_line": "line1",
                    }
                ],
            }
        )


@pytest.mark.asyncio
async def test_file_not_exists(handler, tmp_path):
    """Test handling of non-existent file."""
    file_path = str(tmp_path / "nonexistent.txt")

    with pytest.raises(RuntimeError, match="File does not exist"):
        await handler.run_tool(
            {
                "file_path": file_path,
                "insertions": [
                    {
                        "content_to_insert": "new_line",
                        "position": "after",
                        "context_line": "line1",
                        "line_number": 1,
                    }
                ],
            }
        )
