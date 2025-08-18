I would like to add a flag `--mode` that can be used when starting this MCP server, to change various aspects of the MCP server's behaviour.

Sample usage:
```sh
# currently we start the server like this 
mcp-text-editor

# now i would like to be able to pass an optional flag --mode, eg.
mcp-text-editor --mode claude-code

# if an unrecongised flag or argument is passed, the server should fail to start up and show a meaningful error message
```

Possible values passed to this flag: for now, only `--mode claude-code`. We may add more in the future.

Behaviour when `--mode claude-code` is passed:
- Only tool available should be `patch_text_file_contents`
- It must be the only tool listed when calling the `tools/list` API of the server 

Open questions that I need you to check and give input on while planning:
- When the server is started with `--mode claude-code`, could there be any hints, tool descriptions, instructions etc. that mention the other unavailable tools?

Don't code yet, give an overview of what you understand and your high level plan to tackle the problem. 
If necessary, ask questions to establish all relevant context and highlight any blind spots or things I may have missed or gotten wrong. You do NOT need to ask questions if you don't have any.
If there are multiple good options, please present them to me with the pros and cons.
