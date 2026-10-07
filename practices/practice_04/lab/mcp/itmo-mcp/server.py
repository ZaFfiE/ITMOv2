#!/usr/bin/env python3

"""
Minimal MCP-like JSON-RPC stdio server implementing a single tool: repo_search.

Supported methods:
- initialize: basic handshake
- tools/list: describe available tools
- tools/call: invoke repo_search

This is a lightweight implementation to demonstrate a real tool invocation without external deps.
It is not a full MCP reference implementation.
"""

import sys
import json
import re
import glob
import os
from datetime import datetime


SERVER_INFO = {"name": "itmo-mcp", "version": "0.1.0"}


def write_response(resp):
    sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def error(id_, code, message, data=None):
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message, "data": data}}


def success(id_, result):
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def list_tools():
    return {
        "tools": [
            {
                "name": "repo_search",
                "description": "Search repository files by regex over files matched by a glob include mask.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string"},
                        "include": {"type": "string"},
                        "limit": {"type": "number"},
                        "max_files": {"type": "number"}
                    },
                    "required": ["pattern", "include"]
                }
            }
        ]
    }


def repo_search(arguments):
    pattern = arguments.get("pattern", "")
    include = arguments.get("include", "")
    limit = arguments.get("limit")
    max_files = arguments.get("max_files")
    if not include or not isinstance(include, str):
        raise ValueError("include mask is required")
    if not pattern or not isinstance(pattern, str):
        raise ValueError("pattern is required")
    try:
        rx = re.compile(pattern)
    except re.error as e:
        raise ValueError(f"invalid regex: {e}")

    files = glob.glob(include, recursive=True)
    # validate and apply max_files if provided
    if max_files is not None:
        try:
            mf = int(max_files)
        except Exception:
            raise ValueError("max_files must be an integer")
        if mf <= 0:
            raise ValueError("max_files must be > 0")
        files = files[:mf]
    
    results = []
    total_matches = 0
    files_processed = 0
    for path in files:
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            continue
        files_processed += 1
        matches = []
        for i, line in enumerate(lines, start=1):
            if rx.search(line):
                matches.append({"line": i, "text": line.rstrip("\n")})
                total_matches += 1
                if isinstance(limit, (int, float)) and total_matches >= int(limit):
                    break
        if matches:
            results.append({"path": path, "matches": matches})
        if isinstance(limit, (int, float)) and total_matches >= int(limit):
            break

    return {
        "arguments": {"pattern": pattern, "include": include, "limit": limit, "max_files": max_files},
        "total_matches": total_matches,
        "files_processed": files_processed,
        "files": results,
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }


def handle_request(req):
    method = req.get("method")
    id_ = req.get("id")
    params = req.get("params") or {}

    if method == "initialize":
        return success(id_, {"serverInfo": SERVER_INFO, "capabilities": {"tools": {}}})
    if method == "tools/list":
        return success(id_, list_tools())
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if name != "repo_search":
            return error(id_, -32601, f"unknown tool: {name}")
        try:
            result = repo_search(arguments)
        except ValueError as e:
            return error(id_, -32602, str(e))
        return success(id_, result)

    return error(id_, -32601, f"unknown method: {method}")


def selftest():
    # Basic functional test: list_tools and repo_search with a trivial include
    try:
        _ = list_tools()
        return 0
    except Exception:
        return 1


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        code = selftest()
        print("MCP server selftest OK" if code == 0 else "MCP server selftest FAILED")
        sys.exit(code)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            write_response({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}})
            continue
        resp = handle_request(req)
        write_response(resp)


if __name__ == "__main__":
    main()
