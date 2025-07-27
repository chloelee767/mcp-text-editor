# Development Guide

## Development Architecture

This document covers development-specific architectural details, tooling, and patterns for contributing to the MCP Text Editor Server.

## Code Organization Patterns

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
├── test_*.py                      # Unit tests per module
└── test_*_handler.py              # Handler-specific tests
```

#### Test Categories
1. **Unit Tests**: Individual function testing
2. **Integration Tests**: Handler → TextEditor → File System
3. **Error Case Tests**: Comprehensive error scenarios
4. **Hash Validation Tests**: Concurrency control testing

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

## Make Targets

### Development Workflow
```bash
make install      # Install all dependencies
make format       # Auto-format code (black + isort + ruff --fix)
make lint         # Check code quality without changes
make typecheck    # Run mypy static analysis
make test         # Run pytest suite
make coverage     # Run tests with coverage report
```

### Pre-commit Workflow
```bash
make check        # lint + typecheck (required before push)
make fix          # Alias for format
make all          # format + typecheck + coverage (comprehensive check)
```

## Architecture Decisions

### Why Handler Pattern?
- **Separation of Concerns**: MCP protocol logic separate from business logic
- **Testability**: Easy to test handlers and core logic independently  
- **Extensibility**: Adding new tools requires minimal changes
- **Consistency**: Uniform structure across all operations

### Why Hash-Based Concurrency?
- **Optimistic Locking**: Better performance than file locking
- **Conflict Detection**: Precise detection of concurrent modifications
- **Atomicity**: All-or-nothing operations for multi-patch requests
- **LLM Friendly**: Clear error messages with actionable suggestions

### Why Line-Oriented Operations?
- **Human Intuitive**: Line numbers more natural than character positions
- **Tool Integration**: Better compatibility with editor tools
- **Precision**: Exact targeting of modifications
- **Efficiency**: Partial file processing reduces memory usage

## Debugging and Development

### Local Testing
```bash
# Start interactive inspector
npx @modelcontextprotocol/inspector mcp-text-editor

# Test specific tool with payload
python call_mcp_tool.py --name patch_text_file_contents --payload-file examples/patch_file.json
```

### Logging Configuration
```python
# In development, adjust logging level
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mcp-text-editor")
```

### Common Development Tasks

#### Adding a New Tool
1. Create handler in `handlers/new_tool.py`
2. Extend `BaseHandler`
3. Define `get_tool_description()` and `run_tool()`
4. Add to `handlers/__init__.py`
5. Register in `server.py`
6. Add tests in `tests/test_new_tool.py`

#### Modifying Core Logic
1. Update `TextEditor` methods in `text_editor.py`
2. Ensure backward compatibility or update all handlers
3. Add comprehensive tests
4. Update API documentation if interface changes

#### Adding New Models
1. Define Pydantic models in `models.py`
2. Use for request/response validation
3. Add model tests in `test_models.py`

## Performance Considerations

### Memory Usage
- File content held in memory only during processing
- Large files processed line-by-line
- No persistent caching between requests

### I/O Patterns
- Single file read per operation
- Atomic write operations
- No temporary file usage

### Optimization Opportunities
- Streaming for very large files
- Content compression for network transfer
- Caching for repeated file access (if needed)

## Security Review Checklist

### Path Security
- [ ] All paths validated for traversal attempts
- [ ] Absolute paths required
- [ ] No symlink following vulnerabilities

### Input Validation  
- [ ] All inputs validated through Pydantic models
- [ ] Hash validation prevents injection
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
- [ ] CHANGELOG.md updated
- [ ] Version bumped appropriately

