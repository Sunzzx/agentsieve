# AgentSieve 🔬

**Zero-LLM, high-speed semantic & AST-aware tool output distiller for autonomous coding agents.**

AgentSieve intercepts, analyzes, and compresses verbose command outputs, test runner logs, Python/Node stack traces, huge JSON payloads, and git diffs before they enter an agent's context window. By stripping out redundant wrapper frames, collapsing non-focused AST bodies, and summarizing list payloads, AgentSieve saves **60–90%** of agent token consumption without requiring external LLM calls or round-trips.

---

## Architecture & Features

- **AST-Aware Code Pruner (`agentsieve/ast_pruner.py`)**: Parses Python code into AST structures, collapsing method and function bodies while preserving signatures, docstrings, classes, imports, and explicitly focused symbols or line numbers.
- **Traceback Distiller (`agentsieve/traceback_distiller.py`)**: Strips standard library (`site-packages`, `lib/python`) and internal framework (`node_modules`) stack frames, isolating actionable user code files, line numbers, and root-cause exceptions.
- **Test Runner Distiller (`agentsieve/test_runner_distiller.py`)**: Parses `pytest` and `cargo test` outputs, extracting failing test assertions and captured errors while discarding thousands of lines of passing test noise.
- **JSON & Structured Data Distiller (`agentsieve/json_distiller.py`)**: Summarizes large API responses and lists into structural schemas with representative head/tail items and keys.
- **Git Diff Distiller (`agentsieve/git_distiller.py`)**: Automatically collapses verbose auto-generated lockfiles (`package-lock.json`, `Cargo.lock`) and bounding diff hunks.
- **Model Context Protocol (MCP) Server (`agentsieve/mcp_server.py`)**: Exposes native JSON-RPC tools (`distill_tool_output`, `distill_code_ast`) for direct agent integration.

---

## Installation

```bash
pip install -e .
```

---

## CLI Usage

### 1. Distill Command Output from Stdin / File
```bash
pytest -v | agentsieve distill
```

### 2. Wrap Shell Execution & Auto-Distill
```bash
agentsieve run -- pytest -v
```

### 3. Inspect Token Weight
```bash
agentsieve inspect output.json
```

---

## Python API

```python
from agentsieve import distill_tool_output, ContentKind

result = distill_tool_output(raw_logs, max_tokens=1500)
print(result.distilled_text)
print(f"Saved {result.saved_tokens} tokens (-{result.savings_percent}%)")
```

---

## License

MIT License © 2026 Sunzzx.
