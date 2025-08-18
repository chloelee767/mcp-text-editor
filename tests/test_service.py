"""Tests for core service logic."""

import os

import pytest

from mcp_text_editor.models import EditFileOperation, EditPatch, EditResult
from mcp_text_editor.service import TextEditorService


@pytest.fixture
def service():
    """Create TextEditorService instance."""
    return TextEditorService()


def test_calculate_hash(service):
    """Test hash calculation."""
    content = "test content"
    hash1 = service.calculate_hash(content)
    hash2 = service.calculate_hash(content)
    assert hash1 == hash2
    assert isinstance(hash1, str)
    assert len(hash1) == 64  # SHA-256 hash length


def test_read_file_contents(service, test_file):
    """Test reading file contents."""
    # Test reading entire file
    content, start, end = service.read_file_contents(test_file)
    assert content == "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"
    assert start == 1
    assert end == 5

    # Test reading specific lines
    content, start, end = service.read_file_contents(test_file, start=2, end=4)
    assert content == "Line 2\nLine 3\nLine 4\n"
    assert start == 2
    assert end == 4


def test_read_file_contents_invalid_file(service):
    """Test reading non-existent file."""
    with pytest.raises(FileNotFoundError):
        service.read_file_contents("nonexistent.txt")


def test_validate_patches(service):
    """Test patch validation."""
    # Valid patches
    patches = [
        EditPatch(start=1, end=2, contents="content1", range_hash="hash1"),
        EditPatch(start=3, end=4, contents="content2", range_hash="hash2"),
    ]
    assert service.validate_patches(patches, 5) is True

    # Overlapping patches
    patches = [
        EditPatch(start=1, end=3, contents="content1", range_hash="hash1"),
        EditPatch(start=2, end=4, contents="content2", range_hash="hash2"),
    ]
    assert service.validate_patches(patches, 5) is False

    # Out of bounds patches
    patches = [EditPatch(start=1, end=10, contents="content1", range_hash="hash1")]
    assert service.validate_patches(patches, 5) is False


