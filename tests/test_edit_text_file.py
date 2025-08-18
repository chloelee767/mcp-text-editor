import pytest

from mcp_text_editor.text_editor import EditPatch, TextEditor

# ============================================================================
# V2 Test Helpers and Fixtures
# ============================================================================

@pytest.fixture
def editor():
    """Create TextEditor instance."""
    return TextEditor()

@pytest.fixture
def test_invalid_encoding_file(tmp_path):
    """Create a temporary file with a custom encoding to test encoding errors."""
    file_path = tmp_path / "invalid_encoding.txt"
    # Create Shift-JIS encoded file that will fail to decode with UTF-8
    test_data = bytes(
        [0x83, 0x65, 0x83, 0x58, 0x83, 0x67, 0x0A]
    )  # "テスト\n" in Shift-JIS
    with open(file_path, "wb") as f:
        f.write(test_data)
    return str(file_path)

def create_v2_patch(old_string: str, new_string: str, start: int, end: int = None):
    """Helper function to create v2 patch format."""
    return {
        "old_string": old_string,
        "new_string": new_string,
        "ranges": [{"start": start, "end": end}]
    }


def create_multi_range_v2_patch(old_string: str, new_string: str, ranges: list):
    """Helper function to create v2 patch with multiple ranges."""
    return {
        "old_string": old_string,
        "new_string": new_string,
        "ranges": ranges
    }


@pytest.fixture
def test_file_v2(tmp_path):
    """Create a test file specifically for v2 testing."""
    file_path = tmp_path / "test_v2.txt"
    content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"
    file_path.write_text(content)
    return file_path

# ============================================================================
# V2 Tests - edit_file_contents_v2
# ============================================================================

@pytest.mark.asyncio
async def test_edit_file_contents_v2_basic_replace(editor, test_file_v2):
    """Test basic single line replacement using v2 API."""
    # Replace "Line 2" with "Modified Line 2"
    patch = create_v2_patch("Line 2\n", "Modified Line 2\n", 2, 2)

    result = await editor.edit_file_contents_v2(str(test_file_v2), [patch])

    assert result["result"] == "ok"
    expected_content = "Line 1\nModified Line 2\nLine 3\nLine 4\nLine 5\n"
    assert test_file_v2.read_text() == expected_content


@pytest.mark.asyncio
async def test_edit_file_contents_v2_multiple_lines(editor, test_file_v2):
    """Test replacing multiple consecutive lines using v2 API."""
    # Replace lines 2-3 with new content
    patch = create_v2_patch("Line 2\nLine 3\n", "New Line 2\nNew Line 3\n", 2, 3)

    result = await editor.edit_file_contents_v2(str(test_file_v2), [patch])

    assert result["result"] == "ok"
    expected_content = "Line 1\nNew Line 2\nNew Line 3\nLine 4\nLine 5\n"
    assert test_file_v2.read_text() == expected_content


@pytest.mark.asyncio
async def test_edit_file_contents_v2_multiple_patches(editor, test_file_v2):
    """Test applying multiple non-overlapping patches using v2 API."""
    patches = [
        create_v2_patch("Line 1\n", "Modified Line 1\n", 1, 1),
        create_v2_patch("Line 3\n", "Modified Line 3\n", 3, 3),
    ]

    result = await editor.edit_file_contents_v2(str(test_file_v2), patches)

    assert result["result"] == "ok"
    expected_content = "Modified Line 1\nLine 2\nModified Line 3\nLine 4\nLine 5\n"
    assert test_file_v2.read_text() == expected_content


@pytest.mark.asyncio
async def test_edit_file_contents_v2_file_not_found(editor, tmp_path):
    """Test v2 API behavior with non-existent file."""
    non_existent = tmp_path / "missing.txt"
    patch = create_v2_patch("old", "new", 1, 1)

    result = await editor.edit_file_contents_v2(str(non_existent), [patch])

    assert result["result"] == "error"
    assert "File not found" in result["reason"]
    assert result.get("suggestion") == "append"


@pytest.mark.asyncio
async def test_edit_file_contents_v2_content_mismatch(editor, test_file_v2):
    """Test v2 API behavior when old_string doesn't match actual content."""
    # Try to replace content that doesn't exist
    patch = create_v2_patch("Wrong Content\n", "New Content\n", 2, 2)

    result = await editor.edit_file_contents_v2(str(test_file_v2), [patch])

    assert result["result"] == "error"
    assert "does not match expected string" in result["reason"]
    # File should be unchanged
    expected_content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"
    assert test_file_v2.read_text() == expected_content


@pytest.mark.asyncio
async def test_edit_file_contents_v2_overlapping_ranges(editor, test_file_v2):
    """Test v2 API detection of overlapping ranges."""
    patches = [
        create_v2_patch("Line 2\n", "New Line 2\n", 2, 2),
        create_v2_patch("Line 2\nLine 3\n", "Overlapping\n", 2, 3),  # Overlaps with first patch
    ]

    result = await editor.edit_file_contents_v2(str(test_file_v2), patches)

    assert result["result"] == "error"
    assert "Overlapping ranges" in result["reason"]
    # File should be unchanged
    expected_content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"
    assert test_file_v2.read_text() == expected_content


@pytest.mark.asyncio
async def test_edit_file_contents_v2_invalid_line_range(editor, test_file_v2):
    """Test v2 API with invalid line ranges."""
    # Try to access line beyond file length
    patch = create_v2_patch("Non-existent\n", "New\n", 10, 10)

    result = await editor.edit_file_contents_v2(str(test_file_v2), [patch])

    assert result["result"] == "error"
    assert "out of range" in result["reason"]


@pytest.mark.asyncio
async def test_edit_file_contents_v2_multi_range_patch(editor, test_file_v2):
    """Test v2 API with multiple ranges in single patch (replace same content in different locations)."""
    # Add duplicate lines to test file first
    test_file_v2.write_text("Line 1\nCommon\nLine 3\nCommon\nLine 5\n")

    # Replace "Common\n" in both locations (lines 2 and 4)
    patch = create_multi_range_v2_patch(
        "Common\n",
        "Replaced\n",
        [{"start": 2, "end": 2}, {"start": 4, "end": 4}]
    )

    result = await editor.edit_file_contents_v2(str(test_file_v2), [patch])

    assert result["result"] == "ok"
    expected_content = "Line 1\nReplaced\nLine 3\nReplaced\nLine 5\n"
    assert test_file_v2.read_text() == expected_content


@pytest.mark.asyncio
async def test_edit_file_contents_v2_overlapping_within_patch(editor, test_file_v2):
    """Test v2 API detection of overlapping ranges within same patch."""
    # Try to create a patch with overlapping ranges
    patch = create_multi_range_v2_patch(
        "Line 2\n",
        "New Line\n",
        [{"start": 2, "end": 2}, {"start": 2, "end": 3}]  # Overlapping ranges
    )

    result = await editor.edit_file_contents_v2(str(test_file_v2), [patch])

    assert result["result"] == "error"
    assert "Overlapping ranges within patch" in result["reason"]
    # File should be unchanged
    expected_content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"
    assert test_file_v2.read_text() == expected_content


@pytest.mark.asyncio
async def test_edit_file_contents_v2_end_none_range(editor, test_file_v2):
    """Test v2 API with end=None (to end of file)."""
    patch = create_v2_patch("Line 4\nLine 5\n", "New End\n", 4, None)

    result = await editor.edit_file_contents_v2(str(test_file_v2), [patch])

    assert result["result"] == "ok"
    expected_content = "Line 1\nLine 2\nLine 3\nNew End\n"
    assert test_file_v2.read_text() == expected_content


@pytest.mark.asyncio
async def test_edit_file_contents_v2_empty_file(editor, tmp_path):
    """Test v2 API with empty file."""
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")

    # Try to replace content in empty file - this should fail with empty file
    patch = create_v2_patch("", "New Content\n", 1, None)

    result = await editor.edit_file_contents_v2(str(empty_file), [patch])

    # Empty files have no lines to match, so this should fail
    assert result["result"] == "error"
    assert "out of range" in result["reason"]


@pytest.mark.asyncio
async def test_edit_file_contents_v2_newline_handling(editor, tmp_path):
    """Test v2 API newline handling - ensuring content gets proper newlines."""
    test_file = tmp_path / "newline_test.txt"
    test_file.write_text("Line 1\nLine 2\n")

    # Replace with content that doesn't have trailing newline
    patch = create_v2_patch("Line 2\n", "No Newline", 2, 2)

    result = await editor.edit_file_contents_v2(str(test_file), [patch])

    assert result["result"] == "ok"
    # v2 should add newline automatically
    assert test_file.read_text() == "Line 1\nNo Newline\n"


@pytest.mark.asyncio
async def test_edit_file_contents_v2_invalid_range_end_before_start(editor, test_file_v2):
    """Test v2 API with invalid range where end < start."""
    patch = create_v2_patch("Line 2\n", "New\n", 3, 2)  # end before start

    result = await editor.edit_file_contents_v2(str(test_file_v2), [patch])

    assert result["result"] == "error"
    assert "out of range" in result["reason"] or "invalid" in result["reason"].lower()


# ============================================================================
# V2 Error Handling Tests
# ============================================================================

@pytest.mark.asyncio
async def test_edit_file_contents_v2_path_traversal_prevention(editor, tmp_path):
    """Test v2 API path traversal prevention."""
    malicious_path = str(tmp_path) + "/../../../etc/passwd"
    patch = create_v2_patch("old", "new", 1, 1)

    with pytest.raises(ValueError, match="Path traversal not allowed"):
        await editor.edit_file_contents_v2(malicious_path, [patch])


@pytest.mark.asyncio
async def test_edit_file_contents_v2_encoding_error(editor, test_invalid_encoding_file):
    """Test v2 API behavior with encoding errors."""
    patch = create_v2_patch("test", "new", 1, 1)

    result = await editor.edit_file_contents_v2(test_invalid_encoding_file, [patch])

    assert result["result"] == "error"
    assert "Error editing file" in result["reason"]


@pytest.mark.asyncio
async def test_edit_file_contents_v2_permission_error(editor, tmp_path, monkeypatch):
    """Test v2 API behavior with permission errors during file write."""
    test_file = tmp_path / "permission_test.txt"
    test_file.write_text("original content\n")

    # Store original open function
    original_open = __builtins__['open'] if isinstance(__builtins__, dict) else __builtins__.open

    def mock_open(file_path, mode="r", **kwargs):
        if mode == "w":
            raise PermissionError("Permission denied")
        # Use original open for read operations
        return original_open(file_path, mode, **kwargs)

    monkeypatch.setattr("builtins.open", mock_open)

    patch = create_v2_patch("original content\n", "new content\n", 1, 1)
    result = await editor.edit_file_contents_v2(str(test_file), [patch])

    assert result["result"] == "error"
    assert "Error editing file" in result["reason"]


@pytest.mark.asyncio
async def test_edit_file_contents_v2_io_error_during_write(editor, tmp_path, monkeypatch):
    """Test v2 API handling of IO errors during file write."""
    test_file = tmp_path / "io_test.txt"
    test_file.write_text("original content\n")

    original_open = open

    def mock_open(file_path, mode="r", **kwargs):
        if mode == "w" and "io_test.txt" in str(file_path):
            raise IOError("Disk full")
        return original_open(file_path, mode, **kwargs)

    monkeypatch.setattr("builtins.open", mock_open)

    patch = create_v2_patch("original content\n", "new content\n", 1, 1)
    result = await editor.edit_file_contents_v2(str(test_file), [patch])

    assert result["result"] == "error"
    assert "Error editing file" in result["reason"]
    assert "Disk full" in result["reason"]


@pytest.mark.asyncio
async def test_edit_file_contents_v2_unicode_error_handling(editor, tmp_path):
    """Test v2 API behavior with Unicode encoding issues."""
    test_file = tmp_path / "unicode_test.txt"
    test_file.write_text("unicode: café\n", encoding="utf-8")

    patch = create_v2_patch("unicode: café\n", "unicode: résumé\n", 1, 1)

    # This should work fine with UTF-8
    result = await editor.edit_file_contents_v2(str(test_file), [patch])

    assert result["result"] == "ok"
    assert test_file.read_text(encoding="utf-8") == "unicode: résumé\n"


@pytest.mark.asyncio
async def test_edit_file_contents_v2_unexpected_exception(editor, tmp_path, mocker):
    """Test v2 API handling of unexpected exceptions."""
    test_file = tmp_path / "exception_test.txt"
    test_file.write_text("test content\n")

    # Create two patches to force overlap checking
    patches = [
        create_v2_patch("test content\n", "new content\n", 1, 1),
        create_v2_patch("extra\n", "other\n", 2, 2),  # This will cause overlap checking
    ]

    # Mock the _ranges_overlap method to raise an unexpected error
    def mock_ranges_overlap(*args):
        raise RuntimeError("Unexpected error")

    mocker.patch.object(editor, "_ranges_overlap", mock_ranges_overlap)

    result = await editor.edit_file_contents_v2(str(test_file), patches)

    assert result["result"] == "error"
    assert "Error: Unexpected error" in result["reason"]


# ============================================================================
# V2 Edge Cases and String Validation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_edit_file_contents_v2_exact_string_matching(editor, tmp_path):
    """Test v2 API exact string matching requirements."""
    test_file = tmp_path / "exact_match.txt"
    test_file.write_text("Line with    spaces\nLine 2\n")

    # This should fail - wrong number of spaces
    patch = create_v2_patch("Line with  spaces\n", "Fixed\n", 1, 1)  # Only 2 spaces instead of 4
    result = await editor.edit_file_contents_v2(str(test_file), [patch])

    assert result["result"] == "error"
    assert "does not match expected string" in result["reason"]

    # This should succeed - exact match
    patch = create_v2_patch("Line with    spaces\n", "Fixed\n", 1, 1)  # 4 spaces
    result = await editor.edit_file_contents_v2(str(test_file), [patch])

    assert result["result"] == "ok"
    assert test_file.read_text() == "Fixed\nLine 2\n"


@pytest.mark.asyncio
async def test_edit_file_contents_v2_whitespace_sensitivity(editor, tmp_path):
    """Test v2 API sensitivity to different types of whitespace."""
    test_file = tmp_path / "whitespace.txt"
    test_file.write_text("Line\twith\ttabs\nLine with spaces\n")

    # Try to match tabs with spaces (should fail)
    patch = create_v2_patch("Line    with    tabs\n", "Fixed\n", 1, 1)  # Spaces instead of tabs
    result = await editor.edit_file_contents_v2(str(test_file), [patch])

    assert result["result"] == "error"
    assert "does not match expected string" in result["reason"]

    # Correct tab matching should work
    patch = create_v2_patch("Line\twith\ttabs\n", "Fixed\n", 1, 1)
    result = await editor.edit_file_contents_v2(str(test_file), [patch])

    assert result["result"] == "ok"


@pytest.mark.asyncio
async def test_edit_file_contents_v2_complex_multi_patch_scenario(editor, tmp_path):
    """Test v2 API with complex multi-patch scenario from different patches."""
    test_file = tmp_path / "complex.txt"
    test_file.write_text("Header\nSection A\nContent A\nSection B\nContent B\nFooter\n")

    # Apply multiple patches in one operation
    patches = [
        create_v2_patch("Header\n", "New Header\n", 1, 1),
        create_v2_patch("Section A\nContent A\n", "Modified Section A\nNew Content A\n", 2, 3),
        create_v2_patch("Footer\n", "New Footer\n", 6, 6),
    ]

    result = await editor.edit_file_contents_v2(str(test_file), patches)

    assert result["result"] == "ok"
    expected = "New Header\nModified Section A\nNew Content A\nSection B\nContent B\nNew Footer\n"
    assert test_file.read_text() == expected


@pytest.mark.asyncio
async def test_edit_file_contents_v2_line_ending_variations(editor, tmp_path):
    """Test v2 API with different line ending styles."""
    test_file = tmp_path / "line_endings.txt"
    # Create file with Windows-style line endings
    content = "Line 1\r\nLine 2\r\nLine 3\r\n"
    test_file.write_bytes(content.encode('utf-8'))

    # Note: Python's text mode normalizes line endings when reading
    # So we need to match what Python sees, not what's on disk
    file_content = test_file.read_text()
    lines = file_content.splitlines(keepends=True)

    patch = create_v2_patch(lines[1], "Modified Line 2\n", 2, 2)
    result = await editor.edit_file_contents_v2(str(test_file), [patch])

    assert result["result"] == "ok"


@pytest.mark.asyncio
async def test_edit_file_contents_v2_empty_old_string_replacement(editor, tmp_path):
    """Test v2 API with empty old_string (insertion at specific line)."""
    test_file = tmp_path / "empty_old.txt"
    test_file.write_text("Line 1\n\nLine 3\n")  # Empty line in the middle

    # Replace the empty line with content
    patch = create_v2_patch("\n", "New Content\n", 2, 2)
    result = await editor.edit_file_contents_v2(str(test_file), [patch])

    assert result["result"] == "ok"
    assert test_file.read_text() == "Line 1\nNew Content\nLine 3\n"


@pytest.mark.asyncio
async def test_edit_file_contents_v2_empty_new_string_deletion(editor, tmp_path):
    """Test v2 API with empty new_string (deletion)."""
    test_file = tmp_path / "delete_via_empty.txt"
    test_file.write_text("Line 1\nDelete Me\nLine 3\n")

    # "Delete" by replacing with empty string
    patch = create_v2_patch("Delete Me\n", "", 2, 2)
    result = await editor.edit_file_contents_v2(str(test_file), [patch])

    assert result["result"] == "ok"
    # Empty string should still get a newline added
    assert test_file.read_text() == "Line 1\n\nLine 3\n"


@pytest.mark.asyncio
async def test_edit_file_contents_v2_single_character_changes(editor, tmp_path):
    """Test v2 API with very small content changes."""
    test_file = tmp_path / "single_char.txt"
    test_file.write_text("x\ny\nz\n")

    patch = create_v2_patch("y\n", "Y\n", 2, 2)
    result = await editor.edit_file_contents_v2(str(test_file), [patch])

    assert result["result"] == "ok"
    assert test_file.read_text() == "x\nY\nz\n"


@pytest.mark.asyncio
async def test_edit_file_contents_v2_partial_line_match_failure(editor, tmp_path):
    """Test v2 API failing when trying to match partial line content."""
    test_file = tmp_path / "partial_match.txt"
    test_file.write_text("This is a long line with specific content\nAnother line\n")

    # Try to match only part of the line - should fail
    patch = create_v2_patch("long line", "short line", 1, 1)
    result = await editor.edit_file_contents_v2(str(test_file), [patch])

    assert result["result"] == "error"
    assert "does not match expected string" in result["reason"]


@pytest.mark.asyncio
async def test_edit_file_contents_v2_identical_old_new_string(editor, tmp_path):
    """Test v2 API behavior when old_string equals new_string."""
    test_file = tmp_path / "identical.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    # Try to "change" line to itself
    patch = create_v2_patch("Line 2\n", "Line 2\n", 2, 2)
    result = await editor.edit_file_contents_v2(str(test_file), [patch])

    # This should succeed (no-op change)
    assert result["result"] == "ok"
    assert test_file.read_text() == "Line 1\nLine 2\nLine 3\n"


@pytest.mark.asyncio
async def test_edit_file_contents_v2_boundary_conditions_first_line(editor, tmp_path):
    """Test v2 API boundary conditions with first line."""
    test_file = tmp_path / "first_line.txt"
    test_file.write_text("First\nSecond\nThird\n")

    patch = create_v2_patch("First\n", "Modified First\n", 1, 1)
    result = await editor.edit_file_contents_v2(str(test_file), [patch])

    assert result["result"] == "ok"
    assert test_file.read_text() == "Modified First\nSecond\nThird\n"


@pytest.mark.asyncio
async def test_edit_file_contents_v2_boundary_conditions_last_line(editor, tmp_path):
    """Test v2 API boundary conditions with last line."""
    test_file = tmp_path / "last_line.txt"
    test_file.write_text("First\nSecond\nLast\n")

    patch = create_v2_patch("Last\n", "Modified Last\n", 3, 3)
    result = await editor.edit_file_contents_v2(str(test_file), [patch])

    assert result["result"] == "ok"
    assert test_file.read_text() == "First\nSecond\nModified Last\n"


# ============================================================================
# V2 Test Coverage Summary
# ============================================================================
#
# The above v2 tests provide comprehensive coverage for edit_file_contents_v2:
#
# Core Functionality (7 tests):
# - Basic single/multiple line replacement
# - Multiple patch operations
# - Multi-range patches (same content in different locations)
# - End=None range handling
# - Newline handling
# - Complex multi-patch scenarios
#
# Error Handling (8 tests):
# - File not found
# - Content mismatch validation
# - Overlapping range detection (within and across patches)
# - Invalid line ranges
# - Path traversal prevention
# - Encoding errors
# - Permission/IO errors
# - Unexpected exception handling
#
# Edge Cases & String Validation (15 tests):
# - Empty file handling
# - Exact string matching requirements
# - Whitespace sensitivity (spaces vs tabs)
# - Line ending variations
# - Empty old_string/new_string handling
# - Single character changes
# - Partial line match failures
# - Identical old/new string (no-op)
# - Boundary conditions (first/last line)
# - Unicode handling
#
# Key Differences from V1:
# - V2 requires existing files (no file creation)
# - V2 uses string-based validation instead of hash-based
# - V2 supports multi-range patches in single patch object
# - V2 has different error messages and behaviors
#
# Coverage Status: ✅ COMPREHENSIVE
# The v2 function now has equivalent or better test coverage than v1.
# It's safe to remove the v1 function when ready.
# ============================================================================
