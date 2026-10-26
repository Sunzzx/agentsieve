"""
AST and syntax-aware code distillation.
Extracts structural interfaces, signatures, docstrings, and focus regions while
collapsing unreferenced implementation details to preserve agent token budgets.
"""

from __future__ import annotations
import ast
import re
from typing import Sequence


class ASTCodeDistiller:
    """
    Performs structural code pruning using Python's native AST engine,
    with regex-based structural folding for other programming languages.
    """

    def __init__(self, max_tokens: int = 1500):
        self.max_tokens = max_tokens

    def distill_python(
        self,
        code: str,
        focus_symbols: Sequence[str] | None = None,
        focus_lines: Sequence[int] | None = None,
        keep_docstrings: bool = True,
    ) -> str:
        """
        Distills Python code by pruning method and function bodies,
        preserving imports, class hierarchy, method signatures, return types,
        and full code for explicitly focused symbols or line numbers.
        """
        focus_syms = set(focus_symbols or [])
        focus_lns = set(focus_lines or [])

        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Fall back to structural bracket/indent pruning if code is a partial snippet
            return self._distill_by_indentation(code, focus_syms, focus_lns)

        lines = code.splitlines()
        total_lines = len(lines)
        
        # Identify node spans to collapse
        # A replacement map: start_line (1-indexed) -> (end_line, replacement_text)
        collapses: list[tuple[int, int, str]] = []

        def should_keep_body(node: ast.AST) -> bool:
            # Check if node name or any focused line intersects this node
            name = getattr(node, "name", None)
            if name and name in focus_syms:
                return True
            if focus_lns and hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                for l in range(node.lineno, (node.end_lineno or node.lineno) + 1):
                    if l in focus_lns:
                        return True
            return False

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if should_keep_body(node):
                    continue
                
                # Find where body starts
                body = node.body
                if not body:
                    continue
                
                first_stmt = body[0]
                # If the first statement is a docstring and keep_docstrings is True, keep it
                if keep_docstrings and isinstance(first_stmt, ast.Expr) and isinstance(first_stmt.value, ast.Constant) and isinstance(first_stmt.value.value, str):
                    if len(body) > 1:
                        start_collapse = body[1].lineno
                        end_collapse = node.end_lineno or body[-1].lineno
                        if end_collapse >= start_collapse:
                            collapsed_count = end_collapse - start_collapse + 1
                            indent = " " * getattr(body[1], "col_offset", node.col_offset + 4)
                            collapses.append((start_collapse, end_collapse, f"{indent}... # [{collapsed_count} lines collapsed]"))
                else:
                    start_collapse = first_stmt.lineno
                    end_collapse = node.end_lineno or body[-1].lineno
                    if end_collapse >= start_collapse:
                        collapsed_count = end_collapse - start_collapse + 1
                        indent = " " * getattr(first_stmt, "col_offset", node.col_offset + 4)
                        collapses.append((start_collapse, end_collapse, f"{indent}... # [{collapsed_count} lines collapsed]"))

        if not collapses:
            return code

        # Sort collapses by start_line descending so replacements do not offset indices
        collapses.sort(key=lambda x: x[0], reverse=True)
        
        # Mark lines to keep or replace
        modified_lines = list(lines)
        for start_l, end_l, repl in collapses:
            # 1-indexed to 0-indexed
            idx_start = start_l - 1
            idx_end = end_l
            if 0 <= idx_start < len(modified_lines):
                modified_lines[idx_start:idx_end] = [repl]

        header = f"# [agentsieve: AST skeleton ({total_lines} lines distilled)]\n"
        return header + "\n".join(modified_lines)

    def _distill_by_indentation(
        self,
        code: str,
        focus_syms: set[str],
        focus_lns: set[int],
    ) -> str:
        """Fallback indentation-aware summarizer for code snippets."""
        lines = code.splitlines()
        result = []
        in_collapsed_block = False
        collapsed_lines = 0
        
        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            is_def_or_class = stripped.startswith(("def ", "class ", "async def ", "export ", "function "))
            
            if idx in focus_lns or any(sym in line for sym in focus_syms):
                if in_collapsed_block:
                    result.append(f"    ... # [{collapsed_lines} lines collapsed]")
                    in_collapsed_block = False
                result.append(line)
                continue
                
            if is_def_or_class:
                if in_collapsed_block:
                    result.append(f"    ... # [{collapsed_lines} lines collapsed]")
                    in_collapsed_block = False
                result.append(line)
            elif line.startswith((" ", "\t")) and not in_collapsed_block and not stripped.startswith(""""""):
                in_collapsed_block = True
                collapsed_lines = 1
            elif in_collapsed_block and line.startswith((" ", "\t")):
                collapsed_lines += 1
            else:
                if in_collapsed_block:
                    result.append(f"    ... # [{collapsed_lines} lines collapsed]")
                    in_collapsed_block = False
                result.append(line)
                
        if in_collapsed_block:
            result.append(f"    ... # [{collapsed_lines} lines collapsed]")
            
        return "\n".join(result)


def distill_code(
    code: str,
    language: str = "python",
    focus_symbols: Sequence[str] | None = None,
    focus_lines: Sequence[int] | None = None,
    keep_docstrings: bool = True,
) -> str:
    distiller = ASTCodeDistiller()
    if language.lower() in ("python", "py"):
        return distiller.distill_python(
            code=code,
            focus_symbols=focus_symbols,
            focus_lines=focus_lines,
            keep_docstrings=keep_docstrings,
        )
    return distiller._distill_by_indentation(
        code=code,
        focus_syms=set(focus_symbols or []),
        focus_lns=set(focus_lines or []),
    )
