# MCP Text Editor Server

[![codecov](https://codecov.io/gh/tumf/mcp-text-editor/branch/main/graph/badge.svg?token=52D51U0ZUR)](https://codecov.io/gh/tumf/mcp-text-editor)
[![smithery badge](https://smithery.ai/badge/mcp-text-editor)](https://smithery.ai/server/mcp-text-editor)
[![Glama MCP Server](https://glama.ai/mcp/servers/k44dnvso10/badge)](https://glama.ai/mcp/servers/k44dnvso10)
[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/tumf-mcp-text-editor-badge.png)](https://mseep.ai/app/tumf-mcp-text-editor)

A Model Context Protocol (MCP) server that provides line-oriented text file editing capabilities through a standardized API. Optimized for LLM tools with efficient partial file access to minimize token usage.

## Quick Start for Claude.app Users

Add the following configuration to your Claude desktop config:

```shell
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

```json
{
  "mcpServers": {
    "text-editor": {
      "command": "uvx",
      "args": ["mcp-text-editor"]
    }
  }
}
```

For Claude Code users, enable restricted mode with only the patch tool, since the rest of the tools are redundant with Claude Code's built in tools:

```json
{
  "mcpServers": {
    "text-editor": {
      "command": "uvx", 
      "args": ["mcp-text-editor", "--mode", "claude-code"]
    }
  }
}
```

## Installation

### Via uvx (Recommended)

```bash
uvx mcp-text-editor
```

### Via Smithery

Install automatically for Claude Desktop via [Smithery](https://smithery.ai/server/mcp-text-editor):

```bash
npx -y @smithery/cli install mcp-text-editor --client claude
```

### Via Docker

```bash
docker run -i --rm --mount "type=bind,src=/path/to/files,dst=/path/to/files" mcp/text-editor
```

Build locally:
```bash
docker build --network=host -t mcp/text-editor .
```

## Features

- **Line-oriented editing**: Precise text file operations using line numbers
- **Token-efficient**: Smart partial file access reduces LLM token consumption  
- **Multi-file operations**: Edit multiple files in a single atomic operation
- **Conflict detection**: String-based validation prevents data loss from concurrent edits
- **Encoding support**: Handles various text encodings (UTF-8, Shift_JIS, Latin1, etc.)
- **Safe operations**: Path validation and permission checks prevent unauthorized access

## Available Tools

- **get_text_file_contents**: Read file contents with optional line range specification
- **patch_text_file_contents**: Apply targeted edits using string-based validation
- **create_text_file**: Create new text files
- **append_text_file_contents**: Append content to existing files
- **insert_text_file_contents**: Insert content at specific line positions  
- **delete_text_file_contents**: Delete specific line ranges from files

For detailed API documentation and examples, see [TOOLS.md](TOOLS.md).

## Mode Options

### Default Mode
All tools are available for comprehensive text editing operations.

### Claude Code Mode (`--mode claude-code`)
Restricted mode with only the `patch_text_file_contents` tool available. Designed for integration with Claude Code where built-in file operations handle most editing needs.

## Requirements

- Python 3.13 or higher
- File system permissions for read/write operations
- POSIX-compliant operating system (Linux, macOS) or Windows

## Usage Examples

### Basic File Reading
```json
{
  "files": [
    {
      "file_path": "/path/to/file.txt",
      "ranges": [{"start": 1, "end": 10}]
    }
  ]
}
```

### String-Based Editing
```json
{
  "files": [
    {
      "file_path": "/path/to/file.txt", 
      "patches": [
        {
          "old_string": "old content to replace",
          "new_string": "new content",
          "ranges": [{"start": 5, "end": 5}]
        }
      ]
    }
  ]
}
```

## Security

- **Path validation**: Prevents directory traversal attacks
- **String verification**: Validates exact content matches to prevent data loss
- **Input sanitization**: All inputs validated through type-safe models
- **Permission respect**: Operates within file system permission boundaries

## Documentation

- [TOOLS.md](TOOLS.md) - Complete API reference and examples
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development setup and contribution guide

## Troubleshooting

### Common Issues

**Permission Denied**: Ensure the server process has read/write access to target files and directories.

**String Mismatch**: File content doesn't match expected string. Verify the exact content including whitespace and line endings.

**Encoding Issues**: Verify the file encoding matches the specified encoding parameter. Default is UTF-8.

**Content Validation Error**: The old_string doesn't exactly match the file content. Check for exact whitespace and character matching.

## License

MIT

## Contributing

See [DEVELOPMENT.md](DEVELOPMENT.md) for setup instructions, code style guidelines, and contribution process.
