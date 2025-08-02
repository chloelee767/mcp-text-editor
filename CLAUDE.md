# CLAUDE.md for mcp-text-editor

## Project directories

- `working-docs/`: this folder contains various scratch documents such as prompts and implementation plans. You usually should not read the documents here unless requested by the user.

## Local Testing

Activate virtual env:
```
source .venv/bin/activate
```

```bash
# Test specific tools with payload examples
python call_mcp_tool.py --name patch_text_file_contents --payload-file examples/patch_file.json
python call_mcp_tool.py --name delete_text_file_contents --payload-file examples/delete_file.json
python call_mcp_tool.py --name insert_text_file_contents --payload-file examples/insert_file.json
python call_mcp_tool.py --name append_text_file_contents --payload-file examples/append_file.json
```

Run unit tests:
- If inside the virtualenv: `pytest`
- If outside the virtualenv: `uv run pytest`

## Information that may be useful

`./DEVELOPMENT.md` - use with care, some information may be outdated

`./API_FLOW.md` - tracing the flow of various APIs
