"""Test cases for append_text_file_contents handler."""

import os
from typing import Any, Dict, Generator

import pytest

from mcp_text_editor.server import AppendTextFileContentsHandler
from mcp_text_editor.text_editor import TextEditor

# Initialize handler for tests
append_handler = AppendTextFileContentsHandler()


@pytest.fixture
def test_dir(tmp_path: str) -> str:
    """Create a temporary directory for test files."""
    return str(tmp_path)


@pytest.fixture
def cleanup_files() -> Generator[None, None, None]:
    """Clean up any test files after each test."""
    yield
    # Add cleanup code if needed


@pytest.mark.asyncio
async def test_append_text_file_success(test_dir: str, cleanup_files: None) -> None:
    """Test successful appending to a file."""
    test_file = os.path.join(test_dir, "append_test.txt")
    initial_content = "Initial content\n"
    append_content = "Appended content\n"

    # Create initial file
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(initial_content)

    # Append content using handler with new API format
    arguments: Dict[str, Any] = {
        "file_path": test_file,
        "content_to_append": append_content,
        "expected_file_ending": "Initial content",
    }
    response = await append_handler.run_tool(arguments)

    # Check if content was appended correctly
    with open(test_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert content == initial_content + append_content

    # Parse response to check success
    assert len(response) == 1
    result = response[0].text
    assert '"result": "ok"' in result


@pytest.mark.asyncio
async def test_append_text_file_not_exists(test_dir: str, cleanup_files: None) -> None:
    """Test attempting to append to a non-existent file."""
    test_file = os.path.join(test_dir, "nonexistent.txt")

    # Try to append to non-existent file
    arguments: Dict[str, Any] = {
        "file_path": test_file,
        "content_to_append": "Some content\n",
        "expected_file_ending": "dummy_ending",
    }

    # Should raise error because file doesn't exist
    with pytest.raises(RuntimeError) as exc_info:
        await append_handler.run_tool(arguments)
    assert "File does not exist" in str(exc_info.value)


@pytest.mark.asyncio
async def test_append_text_file_ending_mismatch(
    test_dir: str, cleanup_files: None
) -> None:
    """Test appending with incorrect expected file ending."""
    test_file = os.path.join(test_dir, "ending_test.txt")
    initial_content = "Initial content\n"

    # Create initial file
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(initial_content)

    # Try to append with incorrect expected ending
    arguments: Dict[str, Any] = {
        "file_path": test_file,
        "content_to_append": "New content\n",
        "expected_file_ending": "Wrong ending",
    }

    # Should raise error because ending doesn't match
    with pytest.raises(RuntimeError) as exc_info:
        await append_handler.run_tool(arguments)
    assert "mismatch" in str(exc_info.value).lower() or "expected" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_append_text_file_relative_path(
    test_dir: str, cleanup_files: None
) -> None:
    """Test attempting to append using a relative path."""
    arguments: Dict[str, Any] = {
        "file_path": "relative_path.txt",
        "content_to_append": "Some content\n",
        "expected_file_ending": "dummy_ending",
    }

    # Should raise error because path is not absolute
    with pytest.raises(RuntimeError) as exc_info:
        await append_handler.run_tool(arguments)
    assert "File path must be absolute" in str(exc_info.value)


@pytest.mark.asyncio
async def test_append_text_file_missing_args() -> None:
    """Test appending with missing arguments."""
    # Test missing path
    with pytest.raises(RuntimeError) as exc_info:
        await append_handler.run_tool({"content_to_append": "content\n", "expected_file_ending": "ending"})
    assert "field required" in str(exc_info.value).lower() or "file_path" in str(exc_info.value)

    # Test missing content_to_append
    with pytest.raises(RuntimeError) as exc_info:
        await append_handler.run_tool(
            {"file_path": "/absolute/path.txt", "expected_file_ending": "ending"}
        )
    assert "field required" in str(exc_info.value).lower() or "content_to_append" in str(exc_info.value)

    # Test missing expected_file_ending
    with pytest.raises(RuntimeError) as exc_info:
        await append_handler.run_tool(
            {"file_path": "/absolute/path.txt", "content_to_append": "content\n"}
        )
    assert "field required" in str(exc_info.value).lower() or "expected_file_ending" in str(exc_info.value)


@pytest.mark.asyncio
async def test_append_text_file_custom_encoding(
    test_dir: str, cleanup_files: None
) -> None:
    """Test appending with custom encoding."""
    test_file = os.path.join(test_dir, "encode_test.txt")
    initial_content = "こんにちは\n"
    append_content = "さようなら\n"

    # Create initial file
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(initial_content)

    # Append content using handler with specified encoding
    arguments: Dict[str, Any] = {
        "file_path": test_file,
        "content_to_append": append_content,
        "expected_file_ending": "こんにちは",
        "encoding": "utf-8",
    }
    response = await append_handler.run_tool(arguments)

    # Check if content was appended correctly
    with open(test_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert content == initial_content + append_content

    # Parse response to check success
    assert len(response) == 1
    result = response[0].text
    assert '"result": "ok"' in result


@pytest.mark.asyncio
async def test_append_text_file_multiline_ending(test_dir: str, cleanup_files: None) -> None:
    """Test appending with multiline file where we validate final line only."""
    test_file = os.path.join(test_dir, "multiline_test.txt")
    initial_content = "Line 1\nLine 2\nFinal line\n"
    append_content = "Appended line\n"

    # Create initial file
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(initial_content)

    # Append content using handler - validate only the final line content
    arguments: Dict[str, Any] = {
        "file_path": test_file,
        "content_to_append": append_content,
        "expected_file_ending": "Final line",
    }
    response = await append_handler.run_tool(arguments)

    # Check if content was appended correctly
    with open(test_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert content == initial_content + append_content

    # Parse response to check success
    assert len(response) == 1
    result = response[0].text
    assert '"result": "ok"' in result


@pytest.mark.asyncio
async def test_append_text_file_empty_ending(test_dir: str, cleanup_files: None) -> None:
    """Test appending to file that ends with empty line."""
    test_file = os.path.join(test_dir, "empty_ending_test.txt")
    initial_content = "Content line\n\n"  # Ends with empty line
    append_content = "New content\n"

    # Create initial file
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(initial_content)

    # Append content using handler - empty final line should be empty string
    arguments: Dict[str, Any] = {
        "file_path": test_file,
        "content_to_append": append_content,
        "expected_file_ending": "",  # Empty final line
    }
    response = await append_handler.run_tool(arguments)

    # Check if content was appended correctly
    with open(test_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert content == initial_content + append_content

    # Parse response to check success
    assert len(response) == 1
    result = response[0].text
    assert '"result": "ok"' in result


@pytest.mark.asyncio
async def test_append_text_file_no_final_newline(test_dir: str, cleanup_files: None) -> None:
    """Test appending to file that doesn't end with newline."""
    test_file = os.path.join(test_dir, "no_newline_test.txt")
    initial_content = "Content without newline"  # No final newline
    append_content = "\nAppended content\n"

    # Create initial file
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(initial_content)

    # Append content using handler
    arguments: Dict[str, Any] = {
        "file_path": test_file,
        "content_to_append": append_content,
        "expected_file_ending": "Content without newline",
    }
    response = await append_handler.run_tool(arguments)

    # Check if content was appended correctly
    with open(test_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert content == initial_content + append_content

    # Parse response to check success
    assert len(response) == 1
    result = response[0].text
    assert '"result": "ok"' in result


@pytest.mark.asyncio
async def test_append_text_file_validation_edge_cases(test_dir: str, cleanup_files: None) -> None:
    """Test edge cases for file ending validation."""
    test_file = os.path.join(test_dir, "validation_test.txt")
    
    # Test case 1: File with spaces at end of line
    initial_content = "Content with spaces   \n"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(initial_content)

    arguments: Dict[str, Any] = {
        "file_path": test_file,
        "content_to_append": "New content\n",
        "expected_file_ending": "Content with spaces   ",  # Should match exactly
    }
    response = await append_handler.run_tool(arguments)
    assert '"result": "ok"' in response[0].text

    # Test case 2: With flexible matching (default), missing trailing spaces should succeed
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(initial_content)
    
    arguments_flexible = arguments.copy()
    arguments_flexible["expected_file_ending"] = "Content with spaces"  # Missing trailing spaces
    
    response = await append_handler.run_tool(arguments_flexible)
    assert '"result": "ok"' in response[0].text
    
    # Test case 3: With exact matching, missing trailing spaces should fail
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(initial_content)
    
    arguments_exact = arguments_flexible.copy()
    arguments_exact["require_exact_match"] = True
    
    with pytest.raises(RuntimeError) as exc_info:
        await append_handler.run_tool(arguments_exact)
    assert "mismatch" in str(exc_info.value).lower() or "expected" in str(exc_info.value).lower()
