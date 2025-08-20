# MCP Text Editor Tools Reference

This document provides complete API documentation for all MCP Text Editor tools, including request/response formats and usage examples.

## Overview

The MCP Text Editor Server provides six tools for comprehensive text file manipulation. All tools support multi-file operations and include robust error handling with helpful suggestions.

### General Principles

- **Line-based operations**: All operations use 1-based line numbers
- **Atomic operations**: Multi-file operations are all-or-nothing
- **Encoding support**: Specify encoding per file (default: UTF-8)
- **Path requirements**: All file paths must be absolute

## Tool Reference

### get_text_file_contents

Read the contents of one or more text files with optional line range specification.

**Request Format:**

```json
{
  "files": [
    {
      "file_path": "/absolute/path/to/file.txt",
      "ranges": [
        {"start": 1, "end": 10},
        {"start": 20, "end": 30}
      ],
      "encoding": "utf-8"  // Optional, defaults to utf-8
    }
  ]
}
```

**Parameters:**
- `file_path`: Absolute path to the text file
- `ranges`: Array of line ranges to read
  - `start`: Starting line number (1-based)
  - `end`: Ending line number (inclusive, null for end of file)
- `encoding`: Text encoding (default: "utf-8")

**Response Format:**

```json
{
  "/absolute/path/to/file.txt": {
    "ranges": [
      {
        "content": "Lines 1-10 content here...",
        "start": 1,
        "end": 10,
        "total_lines": 50,
        "content_size": 512
      }
    ]
  }
}
```

**Usage Example:**

```json
{
  "files": [
    {
      "file_path": "/home/user/config.py",
      "ranges": [
        {"start": 1, "end": null}  // Read entire file
      ]
    }
  ]
}
```

---

### patch_text_file_contents

Apply patches to text files using string-based validation. This is the primary editing tool, especially in Claude Code mode.

**Request Format:**

```json
{
  "files": [
    {
      "file_path": "/absolute/path/to/file.txt",
      "encoding": "utf-8",  // Optional
      "require_exact_match": false,  // Optional
      "patches": [
        {
          "old_string": "exact content to replace",
          "new_string": "new content to insert",
          "ranges": [{"start": 5, "end": 8}]
        }
      ]
    }
  ]
}
```

**Parameters:**
- `file_path`: Absolute path to the file to edit
- `encoding`: Text encoding (default: "utf-8")
- `require_exact_match`: Whether to require exact whitespace matching (default: false). When false, trailing whitespace on each line is ignored when matching old_string. When true, users MUST carefully count and ensure whitespace matches exactly.
- `patches`: Array of patch operations
  - `old_string`: Exact text content to be replaced
  - `new_string`: New content to replace with
  - `ranges`: Line ranges where this patch applies

**Important Notes:**
1. `old_string` must match the file content exactly. By default, trailing whitespace is ignored per line (require_exact_match=false). When require_exact_match=true, whitespace must match exactly.
2. Patches are applied from highest to lowest line number to handle line shifts
3. Patches within a file must not have overlapping ranges
4. Multi-range patches apply the same string replacement to all specified ranges

**Success Response:**

```json
{
  "/absolute/path/to/file.txt": {
    "result": "ok"
  }
}
```

**Error Response:**

```json
{
  "/absolute/path/to/file.txt": {
    "result": "error",
    "reason": "Content mismatch at lines 5-8",
    "suggestion": "check_content",
    "hint": "The old_string doesn't match the actual file content"
  }
}
```

**Usage Examples:**

Single line replacement:
```json
{
  "files": [
    {
      "file_path": "/home/user/app.py",
      "patches": [
        {
          "old_string": "debug = False",
          "new_string": "debug = True",
          "ranges": [{"start": 10, "end": 10}]
        }
      ]
    }
  ]
}
```

Multi-line replacement:
```json
{
  "files": [
    {
      "file_path": "/home/user/config.py",
      "patches": [
        {
          "old_string": "def old_function():\n    return \"old\"",
          "new_string": "def new_function():\n    return \"updated\"",
          "ranges": [{"start": 15, "end": 16}]
        }
      ]
    }
  ]
}
```

---

### create_text_file

Create new text files with specified content.

**Request Format:**

```json
{
  "file_path": "/absolute/path/to/new_file.txt",
  "contents": "Initial file content here...",
  "encoding": "utf-8"  // Optional
}
```

**Parameters:**
- `file_path`: Absolute path for the new file
- `contents`: Initial content for the file
- `encoding`: Text encoding (default: "utf-8")

**Response Format:**

```json
{
  "result": "ok"
}
```

**Usage Example:**

```json
{
  "file_path": "/home/user/new_config.py",
  "contents": "# Configuration file\nDEBUG = True\nPORT = 8000\n"
}
```

---

### append_text_file_contents

Append content to the end of existing files with final-line validation.

**Request Format:**

```json
{
  "file_path": "/absolute/path/to/file.txt",
  "content_to_append": "Content to append...",
  "expected_file_ending": "last line of file",
  "encoding": "utf-8",  // Optional
  "require_exact_match": false  // Optional
}
```

**Parameters:**
- `file_path`: Absolute path to the file
- `content_to_append`: Content to append to the file
- `expected_file_ending`: Expected content of the final line for validation
- `encoding`: Text encoding (default: "utf-8")
- `require_exact_match`: Whether to require exact whitespace matching (default: false). When false, trailing whitespace is ignored when matching expected_file_ending. When true, users MUST carefully count and ensure whitespace matches exactly.

**Response Format:**

```json
{
  "result": "ok"
}
```

**Usage Example:**

```json
{
  "file_path": "/home/user/log.txt",
  "content_to_append": "\nNew log entry: Operation completed\n",
  "expected_file_ending": "Previous log entry here"
}
```

---

### insert_text_file_contents

Insert content at specific line positions with context validation.

**Request Format:**

```json
{
  "file_path": "/absolute/path/to/file.txt",
  "insertions": [
    {
      "content_to_insert": "Content to insert...",
      "position": "after",  // "after" or "before"
      "context_line": "Expected line content",
      "line_number": 10
    }
  ],
  "encoding": "utf-8",  // Optional
  "require_exact_match": false  // Optional
}
```

**Parameters:**
- `file_path`: Absolute path to the file
- `insertions`: Array of insertion operations
  - `content_to_insert`: Content to insert
  - `position`: "after" or "before" the reference line
  - `context_line`: Expected content of the reference line
  - `line_number`: Line number of the reference line
- `encoding`: Text encoding (default: "utf-8")
- `require_exact_match`: Whether to require exact whitespace matching (default: false). When false, trailing whitespace is ignored when matching context_line. When true, users MUST carefully count and ensure whitespace matches exactly.

**Response Format:**

```json
{
  "result": "ok"
}
```

**Usage Example:**

```json
{
  "file_path": "/home/user/functions.py",
  "insertions": [
    {
      "content_to_insert": "def new_helper_function():\n    pass\n\n",
      "position": "after",
      "context_line": "# End of existing functions",
      "line_number": 25
    }
  ]
}
```

---

### delete_text_file_contents

Delete specified line ranges from files with string-based validation.

**Request Format:**

```json
{
  "file_path": "/absolute/path/to/file.txt",
  "deletions": [
    {
      "expected_content": "exact content to delete",
      "ranges": [
        {"start": 10, "end": 15}
      ]
    }
  ],
  "encoding": "utf-8",  // Optional
  "require_exact_match": false  // Optional
}
```

**Parameters:**
- `file_path`: Absolute path to the file
- `deletions`: Array of deletion operations
  - `expected_content`: Exact content expected to be deleted
  - `ranges`: Line ranges where this content should be deleted
    - `start`: Starting line number (1-based)
    - `end`: Ending line number (inclusive)
- `encoding`: Text encoding (default: "utf-8")
- `require_exact_match`: Whether to require exact whitespace matching (default: false). When false, trailing whitespace is ignored when matching expected_content. When true, users MUST carefully count and ensure whitespace matches exactly.

**Response Format:**

```json
{
  "result": "ok"
}
```

**Usage Example:**

```json
{
  "file_path": "/home/user/old_code.py", 
  "deletions": [
    {
      "expected_content": "def deprecated_function():\n    # This function is no longer used\n    pass\n",
      "ranges": [
        {"start": 50, "end": 52}
      ]
    }
  ]
}
```

## Error Handling

### Common Error Types

**Path Validation Errors:**
```json
{
  "result": "error",
  "reason": "Path traversal not allowed",
  "hint": "File paths must not contain '..' patterns"
}
```

**Content Validation Errors:**
```json
{
  "result": "error", 
  "reason": "Content validation failed - file was modified",
  "suggestion": "check_content",
  "hint": "Use get_text_file_contents to verify current content"
}
```

**String Mismatch Errors (patch_text_file_contents):**
```json
{
  "result": "error",
  "reason": "Content mismatch at lines 5-8", 
  "suggestion": "check_content",
  "hint": "The old_string doesn't exactly match file content"
}
```

**Encoding Errors:**
```json
{
  "result": "error",
  "reason": "Failed to decode file with utf-8 encoding",
  "hint": "Try specifying the correct encoding for this file"
}
```

### Error Recovery Patterns

1. **For content validation errors**: Use `get_text_file_contents` to verify current content
2. **For string mismatches**: 
   - By default, trailing whitespace is ignored (require_exact_match=false)
   - If require_exact_match=true, ensure exact whitespace and line ending matching
   - Use `get_text_file_contents` to inspect current content
3. **For encoding issues**: Try different encoding or check file format
4. **For permission errors**: Verify file/directory permissions

## Best Practices

### Efficient Workflows

1. **Read before edit**: Always use `get_text_file_contents` to understand current content
2. **Batch operations**: Process multiple files in single requests when possible
3. **Handle conflicts**: Check for content validation errors and verify string matching
4. **Use appropriate tools**: Choose the right tool for each operation type

### Claude Code Mode Considerations

In `--mode claude-code`, only `patch_text_file_contents` is available:
- Uses string-based validation for precise content matching
- More flexible for automated editing scenarios
- By default, trailing whitespace is ignored (require_exact_match=false)
- Set require_exact_match=true for strict whitespace matching when needed
- Ideal for LLM-driven code editing workflows

### Performance Tips

- Use line ranges to read only needed portions of large files
- Leverage multi-file operations to reduce round trips
- Consider encoding specifications for non-UTF-8 files
- Monitor file sizes for memory usage optimization