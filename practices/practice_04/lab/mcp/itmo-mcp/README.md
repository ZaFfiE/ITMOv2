# itmo-mcp

Minimal stdio JSON-RPC server implementing a single tool: repo_search.

Run:
- Self-test: `python3 ./mcp/itmo-mcp/server.py --selftest`
- Interactive (stdio JSON-RPC): send lines with JSON objects.

Methods:
- initialize
- tools/list
- tools/call { name: "repo_search", arguments: { pattern, include, limit? } }

Example calls (using jq and printf):

Success:
1. Start server: `python3 ./mcp/itmo-mcp/server.py`
2. Send:
```
{"jsonrpc":"2.0","id":1,"method":"initialize"}
{"jsonrpc":"2.0","id":2,"method":"tools/list"}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"repo_search","arguments":{"pattern":"AGENTS","include":"**/*.md","limit":5}}}
```

Error (invalid regex):
```
{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"repo_search","arguments":{"pattern":"[","include":"**/*.md"}}}
```

Logs: proofs/mcp/*.log will be produced by the automated tests below.
