# Development Guide

This document covers development setup, architecture, and contribution guidelines for the MCP Text Editor Server.

## Quick Setup

### Requirements

- Python 3.13 or higher
- uv (recommended) or pip

### Installation

1. Clone the repository
2. Create and activate Python virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   uv sync --all-extras
   ```

### Development Workflow

Run all quality checks:
```bash
make all          # format + typecheck + coverage (comprehensive check)
```

Individual commands:
```bash
make format       # Auto-format code (black + isort + ruff --fix)
make lint         # Check code quality without changes  
make typecheck    # Run mypy static analysis
make test         # Run pytest suite
make coverage     # Run tests with coverage report
make check        # lint + typecheck (required before push)
```

## Architecture

### System Overview

The MCP Text Editor Server implements the [Model Context Protocol](https://github.com/modelcontextprotocol/specification) to provide secure, efficient line-oriented text file editing capabilities.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │    │  MCP Server     │    │  File System    │
│  (Claude, etc.) │◄──►│   (Python)      │◄──►│    (Local)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │                        │
        │ JSON-RPC over stdio    │ Validated operations   │
        │                        │                        │
        ▼                        ▼                        ▼
  Tool calls with            String-based conflict     Atomic file
  arguments/responses        detection & validation     operations
```

### Core Components

#### 1. Server Layer (`server.py`)
- **Entry Point**: Main MCP server implementation using `mcp.server.Server`
- **Tool Registration**: Registers all available text editing tools  
- **Request Routing**: Routes tool calls to appropriate handlers
- **Mode Management**: Handles default vs Claude Code mode tool filtering
- **Error Handling**: Centralized exception handling and logging

#### 2. Handler Layer (`handlers/`)
- **Base Handler** (`base.py`): Abstract base class for all tool handlers
- **Tool Handlers**: One handler per MCP tool:
  - `get_text_file_contents.py` - File reading with line ranges
  - `patch_text_file_contents.py` - String-based editing (primary tool)
  - `create_text_file.py` - New file creation
  - `append_text_file_contents.py` - Content appending
  - `insert_text_file_contents.py` - Line-position insertion
  - `delete_text_file_contents.py` - Line range deletion
- **Input Validation**: Validates tool arguments and file paths
- **Response Formatting**: Formats responses according to MCP specification

#### 3. Core Logic Layer (`text_editor.py`)
- **TextEditor Class**: Main business logic for file operations
- **Security**: Path validation and sanitization
- **Concurrency Control**: String-based conflict detection
- **Encoding Support**: Multi-encoding file handling

#### 4. Service Layer (`service.py`)
- **TextEditorService**: Additional service abstractions
- **Utility Functions**: Common operations and helpers

#### 5. Models Layer (`models.py`)
- **Pydantic Models**: Type-safe data structures
- **Request/Response Objects**: Structured API contracts
- **Validation**: Automatic input validation

### Directory Structure

```
src/mcp_text_editor/
├── server.py              # MCP server entry point and routing
├── text_editor.py         # Core file operation logic
├── service.py             # Service layer abstractions
├── models.py              # Pydantic data models
├── version.py             # Version information
├── args.py                # Command line argument parsing
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

### Design Principles

#### Security First
- **Path Validation**: Prevents directory traversal attacks (`..` patterns)
- **Absolute Paths**: Requires absolute file paths to prevent ambiguity
- **Input Sanitization**: All inputs validated through Pydantic models
- **Error Isolation**: Sensitive information not exposed in error messages

#### Concurrency Safety  
- **String-based Validation**: Exact content matching detects conflicts
- **Atomic Operations**: Multi-patch operations are all-or-nothing
- **Conflict Detection**: Prevents data loss from concurrent modifications

#### LLM Optimization
- **Partial File Access**: Read specific line ranges to minimize token usage
- **Efficient Updates**: Target specific ranges rather than full file replacement
- **Smart Suggestions**: Recommends appropriate tools for different operations

#### Extensibility
- **Handler Pattern**: Easy to add new file operations
- **Layered Architecture**: Clean separation of concerns
- **Protocol Agnostic**: Core logic independent of MCP implementation

## Mode Configuration

The server supports two operational modes controlled by the `--mode` flag:

### Default Mode (No --mode flag)
All six tools are available:
- `get_text_file_contents`
- `patch_text_file_contents` 
- `create_text_file`
- `append_text_file_contents`
- `insert_text_file_contents`
- `delete_text_file_contents`

### Claude Code Mode (`--mode claude-code`)
Only `patch_text_file_contents` is available. This mode is designed for:
- Integration with Claude Code
- String-based validation for precise conflict detection
- Streamlined editing workflows focused on patch operations
- Reduced tool complexity for automated editing scenarios

#### Mode Implementation

Mode selection is handled in `ToolManager` class (`server.py`):

```python
def get_available_tools(self) -> List[Tool]:
    if self.mode == "claude-code":
        return self.claude_code_tools  # Only patch tool
    return self.all_tools  # All tools
```

## Development Patterns

### Handler Pattern
All MCP tools follow a consistent handler pattern:

```python
class SomeHandler(BaseHandler):
    name = "tool_name"
    description = "Tool description"
    
    def get_tool_description(self) -> Tool:
        # Define MCP tool schema
        
    async def run_tool(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        # Validate inputs
        # Delegate to TextEditor
        # Format response
```

### Error Handling Strategy
- **Validation Errors**: Caught early in handlers
- **Business Logic Errors**: Handled in TextEditor with structured responses
- **System Errors**: Logged and converted to user-friendly messages
- **Suggestions**: Each error includes helpful suggestions for alternative approaches

### Testing Patterns

#### Test Organization
```
tests/
├── conftest.py                    # Shared fixtures
└── test_*.py                      # Various types of tests
```

#### Test Categories
1. **Unit Tests**: Individual function testing
2. **Integration Tests**: Handler → TextEditor → File System  
3. **Error Case Tests**: Comprehensive error scenarios
4. **Content Validation Tests**: Concurrency control testing

#### Common Test Patterns
```python
# Fixture for temporary files
@pytest.fixture
def temp_file(tmp_path):
    file_path = tmp_path / "test.txt"
    return file_path

# Async handler testing
@pytest.mark.asyncio
async def test_handler_operation():
    handler = SomeHandler()
    result = await handler.run_tool(arguments)
    assert result[0].text == expected_json
```

## Local Testing Tools

### MCP Inspector
```bash
# Start interactive inspector
npx @modelcontextprotocol/inspector mcp-text-editor

# Test with specific mode
npx @modelcontextprotocol/inspector mcp-text-editor --mode claude-code
```

### Direct Tool Testing
```bash
# Test specific tools with payload examples
python call_mcp_tool.py --name patch_text_file_contents --payload-file examples/patch_file.json
python call_mcp_tool.py --name get_text_file_contents --payload-file examples/get_file_contents.json

# Test with mode flag
python call_mcp_tool.py --name patch_text_file_contents --payload-file examples/patch_file.json --server-command 'mcp-text-editor --mode claude-code'
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mcp_text_editor --cov-report=term-missing

# Run specific test file
pytest tests/test_text_editor.py -v
```

## Contributing

### Code Quality Requirements

All code must pass:
- **Black**: Code formatting
- **isort**: Import sorting  
- **Ruff**: Linting and code quality
- **mypy**: Static type checking
- **pytest**: Test suite with good coverage

Run `make check` before submitting pull requests.

### Adding New Tools

1. Create handler in `handlers/new_tool.py`
2. Extend `BaseHandler` class
3. Define `get_tool_description()` and `run_tool()`
4. Add to `handlers/__init__.py`
5. Register in `server.py` ToolManager
6. Add tests in `tests/test_new_tool.py`
7. Update documentation

### Modifying Core Logic

1. Update `TextEditor` methods in `text_editor.py`
2. Ensure backward compatibility or update all handlers
3. Add comprehensive tests
4. Update API documentation if interface changes

### Adding New Models

1. Define Pydantic models in `models.py`
2. Use for request/response validation
3. Add model tests in `test_models.py`

## Performance Considerations

### Memory Usage
- File content held in memory only during processing
- Large files processed line-by-line when possible
- No persistent caching between requests

### I/O Patterns  
- Single file read per operation
- Atomic write operations
- No temporary file usage

### Concurrency Model
- Each request handled independently
- No shared mutable state between requests
- File system provides isolation
- String-based optimistic concurrency control

## Security Review Checklist

### Path Security
- [ ] All paths validated for traversal attempts
- [ ] Absolute paths required
- [ ] No symlink following vulnerabilities

### Input Validation
- [ ] All inputs validated through Pydantic models  
- [ ] String validation prevents injection
- [ ] Encoding validation prevents errors

### Error Handling
- [ ] No sensitive information in error messages
- [ ] Consistent error response format
- [ ] Proper exception isolation

## Release Process

### Version Management
- Version defined in `src/mcp_text_editor/version.py`
- Automatically picked up by hatchling
- Follow semantic versioning

### Pre-release Checklist  
- [ ] All tests passing (`make test`)
- [ ] Code quality checks passing (`make check`)
- [ ] Coverage requirements met (`make coverage`)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped appropriately
