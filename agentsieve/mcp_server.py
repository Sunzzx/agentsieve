"""
MCP (Model Context Protocol) Server implementation for AgentSieve.
Enables autonomous coding agents to invoke AST and tool output distillation via standard JSON-RPC.
"""

from __future__ import annotations
import sys
import json
from typing import Any
from agentsieve.core import AgentSieve, ContentKind


def handle_mcp_request(request_line: str, sieve: AgentSieve) -> str | None:
    try:
        req = json.loads(request_line)
    except Exception:
        return None

    req_id = req.get("id")
    method = req.get("method")

    if method == "initialize":
        return json.dumps({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "agentsieve-mcp", "version": "0.1.0"}
            }
        })

    if method == "tools/list":
        return json.dumps({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "distill_tool_output",
                        "description": "Distills verbose command logs, test failures, or API payloads to save agent context tokens.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string", "description": "Raw output text"},
                                "max_tokens": {"type": "integer", "description": "Token budget", "default": 1500},
                            },
                            "required": ["text"]
                        }
                    },
                    {
                        "name": "distill_code_ast",
                        "description": "Extracts structural AST skeleton, signatures, and docstrings of source code while collapsing non-focused bodies.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string", "description": "Source code"},
                                "focus_symbols": {"type": "array", "items": {"type": "string"}, "description": "Symbols to preserve in full"},
                                "focus_lines": {"type": "array", "items": {"type": "integer"}, "description": "Line numbers to preserve in full"}
                            },
                            "required": ["code"]
                        }
                    }
                ]
            }
        })

    if method == "tools/call":
        params = req.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {})

        if name == "distill_tool_output":
            text = args.get("text", "")
            max_tokens = args.get("max_tokens", 1500)
            res = sieve.distill(text, max_tokens=max_tokens)
            return json.dumps({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {"type": "text", "text": res.distilled_text}
                    ],
                    "metadata": {
                        "saved_tokens": res.saved_tokens,
                        "savings_percent": res.savings_percent,
                        "kind": res.kind.value,
                    }
                }
            })

        if name == "distill_code_ast":
            code = args.get("code", "")
            focus_symbols = args.get("focus_symbols", [])
            focus_lines = args.get("focus_lines", [])
            res = sieve.distill(code, kind=ContentKind.CODE, focus_symbols=focus_symbols, focus_lines=focus_lines)
            return json.dumps({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {"type": "text", "text": res.distilled_text}
                    ],
                    "metadata": {
                        "saved_tokens": res.saved_tokens,
                        "savings_percent": res.savings_percent,
                    }
                }
            })

    return json.dumps({
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method {method} not found"}
    })


def run_mcp_server():
    """Runs stdin/stdout MCP JSON-RPC loop."""
    sieve = AgentSieve()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        resp = handle_mcp_request(line, sieve)
        if resp:
            sys.stdout.write(resp + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    run_mcp_server()
