# MCP Text Editor API Flow Documentation

## Overview

This document details the execution flow for each MCP tool provided by the text editor server, showing how requests flow through the system components.

## General Request Flow

All tool calls follow this general pattern:

```
MCP Client → server.py → Handler → TextEditor → File System → Response Chain
```

1. **MCP Client** sends JSON-RPC request over stdio
2. **Server** (`server.py`) receives and routes to handler
3. **Handler** validates input and delegates to core logic
4. **TextEditor** performs file operations with safety checks
5. **Response** propagates back through the chain

## Tool-Specific Flows

### `patch_text_file_contents`

The most complex operation, applying targeted modifications to files using string-based validation.

#### Flow Details

```mermaid
sequenceDiagram
    participant Client as MCP Client
    participant Server as server.py
    participant Handler as PatchHandler
    participant Editor as TextEditor
    participant FS as File System

    Client->>Server: patch_text_file_contents(files)
    Server->>Handler: run_tool(arguments)
    
    Handler->>Handler: Validate arguments
    Handler->>Handler: Check files is non-empty array
    
    loop For each file operation
        Handler->>Handler: Check file_path is absolute
        Handler->>Handler: Verify file exists
        
        Handler->>Editor: edit_file_contents_v2(file_path, patches, encoding)
        
        Editor->>FS: Read current file content
        FS-->>Editor: File content
        
        Editor->>Editor: Validate range overlaps (intra and inter-patch)
        
        alt Overlapping ranges detected
            Editor-->>Handler: Error: Overlapping ranges
        else No overlaps
            Editor->>Editor: Sort patches by highest line number
            
            loop For each patch
                loop For each range in patch
                    Editor->>Editor: Validate old_string matches actual content
                    alt String mismatch
                        Editor-->>Handler: Error: Content mismatch
                    else String matches
                        Editor->>Editor: Apply new_string to range
                    end
                end
            end
            
            Editor->>FS: Write modified content atomically
            Editor->>Editor: Calculate new file hash
            Editor-->>Handler: Success response with new hash
        end
    end
    
    Handler-->>Server: JSON response with results for all files
    Server-->>Client: MCP response
```

#### Key Code Locations
- **Entry**: `server.py:65` → `patch_file_handler.run_tool()`
- **Validation**: `handlers/patch_text_file_contents.py:90-131`
- **Core Logic**: `text_editor.py:501` → `edit_file_contents_v2()`
- **String Validation**: `text_editor.py:619-625`
- **Multi-range Processing**: `text_editor.py:627-645`

### `get_text_file_contents`

Retrieves file content with optional line range specification.

#### Flow Details

```mermaid
sequenceDiagram
    participant Client as MCP Client
    participant Server as server.py
    participant Handler as GetHandler
    participant Editor as TextEditor
    participant FS as File System

    Client->>Server: get_text_file_contents(file_path, line_start, line_end)
    Server->>Handler: run_tool(arguments)
    
    Handler->>Handler: Validate arguments
    Handler->>Editor: read_file_contents(file_path, start, end, encoding)
    
    Editor->>Editor: Validate file path
    Editor->>FS: Read file with specified encoding
    FS-->>Editor: File lines
    
    Editor->>Editor: Extract specified line range
    Editor->>Editor: Calculate content hash
    Editor->>Editor: Calculate file statistics
    
    Editor-->>Handler: Content + metadata
    Handler-->>Server: Formatted response
    Server-->>Client: Content with hash and metadata
```

#### Key Code Locations
- **Entry**: `server.py:55` → `get_contents_handler.run_tool()`
- **Core Logic**: `text_editor.py:185` → `read_file_contents()`
- **File Reading**: `text_editor.py:98` → `_read_file()`

### `create_text_file`

Creates new files with specified content.

#### Flow Details

```mermaid
sequenceDiagram
    participant Client as MCP Client
    participant Server as server.py
    participant Handler as CreateHandler
    participant Editor as TextEditor
    participant FS as File System

    Client->>Server: create_text_file(file_path, contents)
    Server->>Handler: run_tool(arguments)
    
    Handler->>Handler: Validate arguments
    Handler->>Handler: Check file doesn't exist
    
    Handler->>FS: Create parent directories if needed
    Handler->>FS: Write content to new file
    
    Handler->>Editor: Calculate file hash
    Handler-->>Server: Success response with hash
    Server-->>Client: Creation confirmation
```

### `append_text_file_contents`

Appends content to the end of existing files.

#### Flow Details

```mermaid
sequenceDiagram
    participant Client as MCP Client
    participant Server as server.py
    participant Handler as AppendHandler
    participant Editor as TextEditor
    participant FS as File System

    Client->>Server: append_text_file_contents(file_path, file_hash, contents)
    Server->>Handler: run_tool(arguments)
    
    Handler->>Editor: Read current file content
    Editor-->>Handler: Current content + hash
    
    Handler->>Handler: Validate file_hash matches current
    
    alt Hash mismatch
        Handler-->>Server: Error: Hash mismatch
    else Hash matches
        Handler->>FS: Append content to file
        Handler->>Editor: Calculate new hash
        Handler-->>Server: Success with new hash
    end
    
    Server-->>Client: Append result
```

### `insert_text_file_contents`

Inserts content at specific line positions.

#### Flow Details

```mermaid
sequenceDiagram
    participant Client as MCP Client
    participant Server as server.py
    participant Handler as InsertHandler
    participant Editor as TextEditor
    participant FS as File System

    Client->>Server: insert_text_file_contents(file_path, file_hash, contents, after/before)
    Server->>Handler: run_tool(arguments)
    
    Handler->>Editor: insert_text_file_contents(...)
    
    Editor->>Editor: Validate exactly one of after/before specified
    Editor->>FS: Read current file content
    Editor->>Editor: Validate file hash
    
    alt Hash mismatch
        Editor-->>Handler: Error: Hash mismatch
    else Hash matches
        Editor->>Editor: Calculate insertion position
        Editor->>Editor: Insert content at position
        Editor->>FS: Write modified content
        Editor->>Editor: Calculate new hash
        Editor-->>Handler: Success with new hash
    end
    
    Handler-->>Server: Insert result
    Server-->>Client: Response
```

### `delete_text_file_contents`

Deletes specified line ranges from files.

#### Flow Details

```mermaid
sequenceDiagram
    participant Client as MCP Client
    participant Server as server.py
    participant Handler as DeleteHandler
    participant Editor as TextEditor
    participant FS as File System

    Client->>Server: delete_text_file_contents(file_path, file_hash, ranges)
    Server->>Handler: run_tool(arguments)
    
    Handler->>Editor: delete_text_file_contents(request)
    
    Editor->>FS: Read current file content
    Editor->>Editor: Validate file hash
    Editor->>Editor: Sort ranges in reverse order
    Editor->>Editor: Validate no overlapping ranges
    
    loop For each range
        Editor->>Editor: Validate range_hash against content
        Editor->>Editor: Delete range from lines
    end
    
    Editor->>FS: Write modified content
    Editor->>Editor: Calculate new hash
    Editor-->>Handler: Success with new hash
    
    Handler-->>Server: Delete result
    Server-->>Client: Response
```

## Error Handling Flows

### String Mismatch Detection (patch_text_file_contents)

```
Patch Request
        ↓
Read Current File Content
        ↓
Extract Content from Specified Range
        ↓
Compare with old_string
        ↓
    [Mismatch?]
        ↓
Return Error with:
- Line range where mismatch occurred
- Suggestion to check content
- Hint about exact string matching
```

### Hash Mismatch Detection (other operations)

```
File Operation Request
        ↓
Read Current File Content
        ↓
Calculate Current Hash
        ↓
Compare with Expected Hash
        ↓
    [Mismatch?]
        ↓
Return Error with:
- Current hash
- Suggestion to use get_text_file_contents
- Helpful hint message
```

### Path Validation

```
File Path Input
        ↓
Check for ".." patterns
        ↓
Verify absolute path
        ↓
    [Invalid?]
        ↓
Return Error:
"Path traversal not allowed" or
"File path must be absolute"
```

### Encoding Errors

```
File Read Request
        ↓
Attempt read with specified encoding
        ↓
    [UnicodeDecodeError?]
        ↓
Return Error:
"Failed to decode file with {encoding} encoding"
```

## Performance Considerations

### Efficient File Reading
- Files read once per operation
- Line ranges extracted without loading entire file into memory
- Hash calculations performed on-demand

### Atomic Operations
- All write operations are atomic
- Temporary files not used (direct write)
- File locks not explicitly used (relies on OS-level atomicity)

### Memory Usage
- Large files processed line-by-line
- Content held in memory only during processing
- No persistent caching between requests

## Concurrency Model

### Thread Safety
- Each request handled independently
- No shared mutable state between requests
- File system provides isolation

### Conflict Resolution
- String-based validation for patch operations (no hash required)
- Hash-based optimistic concurrency control for other operations
- No explicit locking mechanism
- Client responsible for retry logic on conflicts