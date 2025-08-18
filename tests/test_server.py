"""Tests for the MCP Text Editor Server."""

import json
from pathlib import Path
from typing import List

import pytest
from mcp.server import stdio
from mcp.types import TextContent, Tool
from pytest_mock import MockerFixture

from mcp_text_editor.server import (
    GetTextFileContentsHandler,
    ToolManager,
    app,
    append_file_handler,
    call_tool,
    create_file_handler,
    delete_contents_handler,
    get_contents_handler,
    insert_file_handler,
    list_tools,
    main,
    patch_file_handler,
)


@pytest.fixture
def default_tool_manager():
    """Create a default ToolManager for testing."""
    from argparse import Namespace
    args = Namespace(mode=None)
    return ToolManager(args)


@pytest.fixture
def claude_code_tool_manager():
    """Create a ToolManager for claude-code mode."""
    from argparse import Namespace
    args = Namespace(mode="claude-code")
    return ToolManager(args)


@pytest.mark.asyncio
async def test_list_tools(default_tool_manager):
    """Test tool listing."""
    tools: List[Tool] = await list_tools(default_tool_manager)
    assert len(tools) == 6

    # Verify GetTextFileContents tool
    get_contents_tool = next(
        (tool for tool in tools if tool.name == "get_text_file_contents"), None
    )
    assert get_contents_tool is not None
    assert "file" in get_contents_tool.description.lower()
    assert "contents" in get_contents_tool.description.lower()


@pytest.mark.asyncio
async def test_list_tools_claude_code_mode(claude_code_tool_manager):
    """Test tool listing in claude-code mode."""
    tools: List[Tool] = await list_tools(claude_code_tool_manager)
    assert len(tools) == 1
    assert tools[0].name == "patch_text_file_contents"


@pytest.mark.asyncio
async def test_get_contents_empty_files():
    """Test get_contents handler with empty files list."""
    arguments = {"files": []}
    result = await get_contents_handler.run_tool(arguments)
    assert len(result) == 1
    assert result[0].type == "text"
    # Should return empty JSON object
    assert json.loads(result[0].text) == {}


@pytest.mark.asyncio
async def test_unknown_tool_handler(default_tool_manager):
    """Test handling of unknown tool name."""
    with pytest.raises(ValueError) as excinfo:
        await call_tool("unknown_tool", {}, default_tool_manager)
    assert "Unknown tool: unknown_tool" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_contents_handler(test_file):
    """Test GetTextFileContents handler."""
    args = {"files": [{"file_path": test_file, "ranges": [{"start": 1, "end": 3}]}]}
    result = await get_contents_handler.run_tool(args)
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    content = json.loads(result[0].text)
    assert test_file in content
    range_result = content[test_file]["ranges"][0]
    assert "content" in range_result
    assert "start" in range_result
    assert "end" in range_result
    assert "total_lines" in range_result
    assert "content_size" in range_result


@pytest.mark.asyncio
async def test_get_contents_handler_invalid_file(test_file):
    """Test GetTextFileContents handler with invalid file."""
    # Convert relative path to absolute
    nonexistent_path = str(Path("nonexistent.txt").absolute())
    args = {"files": [{"file_path": nonexistent_path, "ranges": [{"start": 1}]}]}
    with pytest.raises(RuntimeError) as exc_info:
        await get_contents_handler.run_tool(args)
    assert "File not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_call_tool_get_contents(test_file, default_tool_manager):
    """Test call_tool with GetTextFileContents."""
    args = {"files": [{"file_path": test_file, "ranges": [{"start": 1, "end": 3}]}]}
    result = await call_tool("get_text_file_contents", args, default_tool_manager)
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    content = json.loads(result[0].text)
    assert test_file in content
    range_result = content[test_file]["ranges"][0]
    assert "content" in range_result
    assert "start" in range_result
    assert "end" in range_result
    assert "total_lines" in range_result
    assert "content_size" in range_result


@pytest.mark.asyncio
async def test_call_tool_unknown(default_tool_manager):
    """Test call_tool with unknown tool."""
    with pytest.raises(ValueError) as exc_info:
        await call_tool("UnknownTool", {}, default_tool_manager)
    assert "Unknown tool" in str(exc_info.value)


@pytest.mark.asyncio
async def test_call_tool_error_handling(default_tool_manager):
    """Test call_tool error handling."""
    # Test with invalid arguments
    with pytest.raises(RuntimeError) as exc_info:
        await call_tool("get_text_file_contents", {"invalid": "args"}, default_tool_manager)
    assert "Missing required argument" in str(exc_info.value)

    # Convert relative path to absolute
    nonexistent_path = str(Path("nonexistent.txt").absolute())
    with pytest.raises(RuntimeError) as exc_info:
        await call_tool(
            "get_text_file_contents",
            {"files": [{"file_path": nonexistent_path, "ranges": [{"start": 1}]}]},
            default_tool_manager,
        )
    assert "File not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_contents_handler_legacy_missing_args():
    """Test GetTextFileContents handler with legacy single file request missing arguments."""
    with pytest.raises(RuntimeError) as exc_info:
        await get_contents_handler.run_tool({})
    assert "Missing required argument: 'files'" in str(exc_info.value)


@pytest.mark.asyncio
async def test_main_stdio_server_error(mocker: MockerFixture):
    """Test main function with stdio_server error."""
    from argparse import Namespace
    # Mock the stdio_server to raise an exception
    mock_stdio = mocker.patch.object(stdio, "stdio_server")
    mock_stdio.side_effect = Exception("Stdio server error")

    args = Namespace(mode=None)
    with pytest.raises(Exception) as exc_info:
        await main(args)
    assert "Stdio server error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_main_run_error(mocker: MockerFixture):
    """Test main function with app.run error."""
    from argparse import Namespace
    # Mock the stdio_server context manager
    mock_stdio = mocker.patch.object(stdio, "stdio_server")
    mock_context = mocker.MagicMock()
    mock_context.__aenter__.return_value = (mocker.MagicMock(), mocker.MagicMock())
    mock_stdio.return_value = mock_context

    # Mock app.run to raise an exception
    mock_run = mocker.patch.object(app, "run")
    mock_run.side_effect = Exception("App run error")

    args = Namespace(mode=None)
    with pytest.raises(Exception) as exc_info:
        await main(args)
    assert "App run error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_contents_relative_path():
    """Test GetTextFileContents with relative path."""
    handler = GetTextFileContentsHandler()
    with pytest.raises(RuntimeError, match="File path must be absolute:.*"):
        await handler.run_tool(
            {
                "files": [
                    {"file_path": "relative/path/file.txt", "ranges": [{"start": 1}]}
                ]
            }
        )


@pytest.mark.asyncio
async def test_get_contents_absolute_path():
    """Test GetTextFileContents with absolute path."""
    handler = GetTextFileContentsHandler()
    abs_path = str(Path("/absolute/path/file.txt").absolute())

    # Define mock as async function
    async def mock_read_multiple_ranges(*args, **kwargs):
        return []

    # Set up mock
    handler.editor.read_multiple_ranges = mock_read_multiple_ranges

    result = await handler.run_tool(
        {"files": [{"file_path": abs_path, "ranges": [{"start": 1}]}]}
    )
    assert isinstance(result[0], TextContent)


@pytest.mark.asyncio
async def test_call_tool_general_exception(default_tool_manager):
    """Test call_tool with a general exception."""
    # Patch get_contents_handler.run_tool to raise a general exception
    original_run_tool = get_contents_handler.run_tool

    async def mock_run_tool(args):
        raise Exception("Unexpected error")

    try:
        get_contents_handler.run_tool = mock_run_tool
        with pytest.raises(RuntimeError) as exc_info:
            await call_tool("get_text_file_contents", {"files": []}, default_tool_manager)
        assert "Error executing command: Unexpected error" in str(exc_info.value)
    finally:
        # Restore original method
        get_contents_handler.run_tool = original_run_tool


@pytest.mark.asyncio
async def test_call_tool_all_handlers(mocker: MockerFixture, default_tool_manager):
    """Test call_tool with all handlers."""
    # Mock run_tool for each handler
    handlers = [
        create_file_handler,
        append_file_handler,
        delete_contents_handler,
        insert_file_handler,
        patch_file_handler,
    ]

    # Setup mocks for all handlers
    async def mock_run_tool(args):
        return [TextContent(text="mocked response", type="text")]

    for handler in handlers:
        mock = mocker.patch.object(handler, "run_tool")
        mock.side_effect = mock_run_tool

    # Test each handler
    for handler in handlers:
        result = await call_tool(handler.name, {"test": "args"}, default_tool_manager)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].text == "mocked response"


@pytest.mark.asyncio
async def test_call_tool_claude_code_mode_allowed(claude_code_tool_manager):
    """Test call_tool with allowed tool in claude-code mode."""
    # Mock patch_file_handler.run_tool
    original_run_tool = patch_file_handler.run_tool

    async def mock_run_tool(args):
        return [TextContent(text="patched", type="text")]

    try:
        patch_file_handler.run_tool = mock_run_tool
        result = await call_tool("patch_text_file_contents", {"test": "args"}, claude_code_tool_manager)
        assert len(result) == 1
        assert result[0].text == "patched"
    finally:
        patch_file_handler.run_tool = original_run_tool


@pytest.mark.asyncio
async def test_call_tool_claude_code_mode_disallowed(claude_code_tool_manager):
    """Test call_tool with disallowed tool in claude-code mode."""
    with pytest.raises(ValueError) as exc_info:
        await call_tool("get_text_file_contents", {"test": "args"}, claude_code_tool_manager)
    assert "Unknown tool: get_text_file_contents" in str(exc_info.value)
