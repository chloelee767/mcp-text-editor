# CLAUDE.md for mcp-text-editor

## Local Testing

Activate virtual env:
```
source .venv/bin/activate
```

```bash
# Test specific tool with payload
python call_mcp_tool.py --name patch_text_file_contents --payload-file examples/patch_file.json
```

Run unit tests:
- If inside the virtualenv: `pytest`
- If outside the virtualenv: `uv run pytest`

## Information that may be useful

`./DEVELOPMENT.md` - use with care, some information may be outdated

`./API_FLOW.md` - tracing the flow of various APIs
