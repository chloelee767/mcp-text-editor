# MCP Text Editor Server Architecture

## Overview

The MCP Text Editor Server is a Python-based server that implements the [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/specification) to provide line-oriented text file editing capabilities. The architecture is designed to be secure, efficient, and optimized for LLM integration with minimal token usage.

## System Architecture

### High-Level Design

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │    │  MCP Server     │    │  File System    │
│  (Claude, etc.) │◄──►│   (Python)      │◄──►│    (Local)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │                        │
        │ JSON-RPC over stdio    │ Validated operations   │
        │                        │                        │
        ▼                        ▼                        ▼
  Tool calls with            Hash-based conflict      Atomic file
  arguments/responses        detection & validation    operations
```

### Core Components

#### 1. Server Layer (`server.py`)
- **Entry Point**: Main MCP server implementation using `mcp.server.Server`
- **Tool Registration**: Registers all available text editing tools
- **Request Routing**: Routes tool calls to appropriate handlers
- **Error Handling**: Centralized exception handling and logging

#### 2. Handler Layer (`handlers/`)
- **Base Handler** (`base.py`): Abstract base class for all tool handlers
- **Tool Handlers**: One handler per MCP tool (patch, get, create, append, delete, insert)
- **Input Validation**: Validates tool arguments and file paths
- **Response Formatting**: Formats responses according to MCP specification

#### 3. Core Logic Layer (`text_editor.py`)
- **TextEditor Class**: Main business logic for file operations
- **Security**: Path validation and sanitization
- **Concurrency Control**: Hash-based conflict detection
- **Encoding Support**: Multi-encoding file handling

#### 4. Service Layer (`service.py`)
- **TextEditorService**: Additional service abstractions
- **Utility Functions**: Common operations and helpers

#### 5. Models Layer (`models.py`)
- **Pydantic Models**: Type-safe data structures
- **Request/Response Objects**: Structured API contracts
- **Validation**: Automatic input validation

## Directory Structure

```
src/mcp_text_editor/
├── server.py              # MCP server entry point and routing
├── text_editor.py         # Core file operation logic
├── service.py             # Service layer abstractions
├── models.py              # Pydantic data models
├── version.py             # Version information
└── handlers/              # Tool handlers
    ├── __init__.py
    ├── base.py            # Base handler class
    ├── get_text_file_contents.py
    ├── patch_text_file_contents.py
    ├── create_text_file.py
    ├── append_text_file_contents.py
    ├── delete_text_file_contents.py
    └── insert_text_file_contents.py
```

## Design Principles

### 1. Security First
- **Path Validation**: Prevents directory traversal attacks (`..` patterns)
- **Absolute Paths**: Requires absolute file paths to prevent ambiguity
- **Input Sanitization**: All inputs validated through Pydantic models
- **Error Isolation**: Sensitive information not exposed in error messages

### 2. Concurrency Safety
- **Hash-based Validation**: File and range-level SHA-256 hashes detect conflicts
- **Atomic Operations**: Multi-patch operations are all-or-nothing
- **Conflict Detection**: Prevents data loss from concurrent modifications

### 3. LLM Optimization
- **Partial File Access**: Read specific line ranges to minimize token usage
- **Efficient Updates**: Target specific ranges rather than full file replacement
- **Smart Suggestions**: Recommends appropriate tools for different operations

### 4. Extensibility
- **Handler Pattern**: Easy to add new file operations
- **Layered Architecture**: Clean separation of concerns
- **Protocol Agnostic**: Core logic independent of MCP implementation

## Key Features

### Line-Oriented Operations
All operations work with line numbers (1-based indexing) rather than character positions, making them more intuitive for text editing tasks.

### Multi-Encoding Support
Supports various text encodings (utf-8, shift_jis, latin1, etc.) with proper error handling for encoding mismatches.

### Conflict Resolution
Hash-based validation at both file and content range levels ensures data integrity in concurrent editing scenarios.

### Error Handling
Comprehensive error handling with helpful suggestions for alternative operations and clear error messages.

## Security Considerations

### Path Security
- All file paths validated to prevent directory traversal
- Absolute paths required to prevent ambiguous file access
- File system permissions respected

### Data Integrity
- SHA-256 hashing prevents data corruption
- Content validation before modifications
- Atomic write operations

### Access Control
- Relies on file system permissions
- No built-in authentication (handled by MCP client)
- Transparent operation logging

## Performance Characteristics

### Memory Efficiency
- Streams file content rather than loading entire files
- Processes line ranges on-demand
- Minimal memory footprint for large files

### I/O Optimization
- Single read operation per file for hash validation
- Atomic write operations
- Efficient line-based processing

## Protocol Compliance

The server fully implements the MCP specification:
- **Tool Discovery**: Lists available tools via `tools/list`
- **Tool Execution**: Handles `tools/call` requests
- **Error Responses**: Standard MCP error format
- **Capability Declaration**: Declares text editing capabilities

## Extension Points

### Adding New Tools
1. Create handler in `handlers/` directory
2. Extend `BaseHandler` class
3. Register in `server.py`
4. Add to `__init__.py` exports

### Custom Validation
- Extend `models.py` with new Pydantic models
- Add validation logic in handlers
- Implement custom error responses

### Additional Encodings
- Extend encoding support in `TextEditor` class
- Add encoding detection if needed
- Handle encoding-specific edge cases