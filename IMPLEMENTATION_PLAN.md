# Implementation Plan: String-Based Text Editor API

## Overview

This document outlines the plan to migrate the `patch_text_file_contents` API from hash-based validation to string-based validation, making it easier to use while maintaining all existing robustness features.

## Current vs New API Format

### Current Format
```json
{
  "files": [
    {
      "file_path": "file1.txt",
      "hash": "sha256-hash-from-get-contents",
      "encoding": "utf-8",
      "patches": [
        {
          "start": 5,
          "end": 8,
          "range_hash": "sha256-hash-of-content-being-replaced",
          "contents": "New content for lines 5-8\n"
        },
        {
          "start": 15,
          "end": null,
          "range_hash": "sha256-hash-of-content-being-replaced",
          "contents": "Content to append\n"
        }
      ]
    }
  ]
}
```

### New Format
```json
{
  "files": [
    {
      "file_path": "file1.txt",
      "encoding": "utf-8",
      "patches": [
        {
          "old_string": "Existing content to be replaced for lines 5-8 and 10-12\n",
          "new_string": "New content for lines 5-8 and 10-12\n",
          "ranges": [
            { "start": 5, "end": 8 },
            { "start": 10, "end": 12 }
          ]
        },
        {
          "old_string": "Existing content to be replaced\n",
          "new_string": "Content to append\n",
          "ranges": [
            { "start": 15, "end": null }
          ]
        }
      ]
    }
  ]
}
```

## Key Changes

1. **Remove hash fields**: Remove `hash` (file-level) and `range_hash` (patch-level) fields
2. **Replace with string matching**: Use `old_string` to specify expected content directly
3. **Multi-range patches**: Replace single `start`/`end` with `ranges[]` array supporting multiple ranges per patch
4. **Rename content field**: `contents` → `new_string` for clarity

## Implementation Tasks

### 1. Update Data Models (`src/mcp_text_editor/models.py`)

#### Current Handler Schema (to be updated)
The handler currently expects the old format. Need to update the schema to new format.

#### New Models to Add
```python
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
```

### 2. Update Handler (`src/mcp_text_editor/handlers/patch_text_file_contents.py`)

#### Current State
- Handler expects old format with `file_path`, `file_hash`, `patches[]` at top level
- Each patch has `start`, `end`, `range_hash`, `contents`

#### Required Changes
- Update `inputSchema` to expect `files[]` array instead of single file
- Remove `file_hash` from required fields  
- Update patch schema: remove `range_hash`, `start`, `end`; add `old_string`, `new_string`, `ranges[]`
- Update `run_tool` method to loop through files and call updated editor method

### 3. Update Core Logic (`src/mcp_text_editor/text_editor.py`)

#### Current Method: `edit_file_contents`
- Expects: `file_path`, `expected_file_hash`, `patches[]` (old format)
- Located at lines 223-499
- Validates file hash at line 297
- Validates range hash at lines 409-419

#### New Method: `edit_file_contents_v2` 
```python
async def edit_file_contents_v2(
    self,
    file_path: str,
    patches: List[Dict[str, Any]], # New format with old_string/new_string/ranges
    encoding: str = "utf-8",
) -> Dict[str, Any]:
```

#### Key Logic Changes

**Remove File Hash Validation** (lines 297-305):
```python
# Remove this block:
elif current_file_hash != expected_file_hash:
    return self.create_error_response(...)
```

**Replace Range Hash Validation** (lines 409-419):
```python
# Current:
actual_range_hash = self.calculate_hash(target_content)
if actual_range_hash != expected_range_hash:
    return error_response

# New:
expected_content = patch["old_string"] 
actual_content = "".join(target_lines)
if actual_content != expected_content:
    return content_mismatch_error
```

**Add Multi-Range Processing**:
```python
# For each patch with multiple ranges
for patch in patches:
    old_string = patch["old_string"]
    new_string = patch["new_string"]
    ranges = patch["ranges"]
    
    # Validate all ranges contain the expected content
    for range_spec in ranges:
        start_zero = range_spec["start"] - 1
        end_zero = range_spec["end"] - 1 if range_spec["end"] else len(lines)
        actual_content = "".join(lines[start_zero:end_zero + 1])
        if actual_content != old_string:
            return content_mismatch_error
    
    # Apply replacement to all ranges
    for range_spec in sorted(ranges, reverse=True):  # Process in reverse order
        # Apply new_string to this range
```

### 4. Range Overlap Validation Updates

#### Current Logic (lines 322-339)
Works on individual patches with single ranges. Need to extend for:

1. **Intra-patch validation**: Ranges within same patch cannot overlap
2. **Inter-patch validation**: Ranges across different patches cannot overlap

```python
# New validation logic:
all_ranges = []
for patch in patches:
    # 1. Validate ranges within this patch don't overlap
    patch_ranges = patch["ranges"]
    for i in range(len(patch_ranges)):
        for j in range(i + 1, len(patch_ranges)):
            if ranges_overlap(patch_ranges[i], patch_ranges[j]):
                return overlap_error
    
    # 2. Collect all ranges for inter-patch validation
    all_ranges.extend(patch_ranges)

# 3. Validate ranges across patches don't overlap
for i in range(len(all_ranges)):
    for j in range(i + 1, len(all_ranges)):
        if ranges_overlap(all_ranges[i], all_ranges[j]):
            return overlap_error
```

### 5. Update Tests

#### Files to Update
- `tests/test_patch_text_file.py` - Main functionality tests
- `tests/test_patch_text_file_end_none.py` - End-of-file scenarios  
- `tests/test_error_hints.py` - Error message tests
- `tests/test_text_editor.py` - Core editor tests

#### Test Data Migration
```python
# Current test format:
{
    "file_path": "/path/to/file",
    "file_hash": "abc123...", 
    "patches": [
        {
            "start": 1,
            "end": 2,
            "range_hash": "def456...",
            "contents": "new content"
        }
    ]
}

# New test format:
{
    "files": [
        {
            "file_path": "/path/to/file",
            "patches": [
                {
                    "old_string": "existing content",
                    "new_string": "new content", 
                    "ranges": [
                        {"start": 1, "end": 2}
                    ]
                }
            ]
        }
    ]
}
```

#### New Test Cases
- Multi-range patches within single patch
- String mismatch error scenarios
- Multi-file operations
- Range overlap within single patch
- Range overlap across patches

### 6. Update Documentation and Examples

#### Files to Update
- `examples/patch_file.json` - Convert to new format
- Handler description string (lines 20-21)
- Input schema description (lines 27-71)

## Implementation Notes

### String Matching Requirements
- **Exact matching required** - character-for-character including whitespace and newlines
- Empty `old_string` indicates insertion (equivalent to current `range_hash: ""`)

### Multi-Range Patch Semantics
- All ranges in a patch must contain identical content matching `old_string`
- All ranges are replaced with `new_string`
- Useful for replacing repeated content across multiple locations

### Error Message Updates
- "FileHash mismatch" → "File content has changed"
- "Content range hash mismatch" → "Content at specified range does not match expected string"
- Remove hash-related suggestion messages

### Processing Order
- Maintain existing reverse-order processing (lines 313-320) to avoid line number shifts
- Process ranges within each patch in reverse order as well

## Implementation Phases

### Phase 1: Core Data Models and Handler Schema
1. Add new data models to `models.py`
2. Update handler input schema
3. Update handler to parse new format

### Phase 2: Core Editor Logic  
1. Create `edit_file_contents_v2` method
2. Implement string matching validation
3. Add multi-range processing logic
4. Update overlap validation

### Phase 3: Testing and Validation
1. Convert existing tests to new format
2. Add new test cases for multi-range scenarios
3. Test error handling and edge cases

### Phase 4: Documentation and Examples
1. Update example files
2. Update API documentation
3. Update handler descriptions

## Success Criteria

- [ ] API accepts new format without hash fields
- [ ] String-based validation works correctly
- [ ] Multi-range patches function properly
- [ ] All existing error handling preserved with updated messages
- [ ] Overlap validation works for both intra- and inter-patch ranges
- [ ] All tests converted and passing
- [ ] Performance remains acceptable for typical use cases