"""
Core orchestration engine for AgentSieve.
Auto-detects tool result semantics, routes to specialized AST/syntax engines,
and enforces strict token budgets with full metrics.
"""

from __future__ import annotations
import re
from enum import Enum
from typing import Sequence, Any
from pydantic import BaseModel, Field

from agentsieve.token_budget import TokenMetrics, compute_metrics, estimate_tokens
from agentsieve.ast_pruner import distill_code
from agentsieve.traceback_distiller import distill_traceback
from agentsieve.test_runner_distiller import distill_test_output
from agentsieve.json_distiller import distill_json
from agentsieve.git_distiller import distill_git_diff


class ContentKind(str, Enum):
    CODE = "code"
    TRACEBACK = "traceback"
    TEST_RUNNER = "test_runner"
    JSON_DATA = "json_data"
    GIT_DIFF = "git_diff"
    GENERIC_LOG = "generic_log"


class DistillationResult(BaseModel):
    kind: ContentKind
    original_tokens: int
    distilled_tokens: int
    saved_tokens: int
    savings_percent: float
    distilled_text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentSieve:
    """
    High-performance semantic tool output distiller for AI agents.
    """

    def __init__(self, default_max_tokens: int = 2000):
        self.default_max_tokens = default_max_tokens

    def detect_kind(self, text: str) -> ContentKind:
        """Auto-detects the content format of the input text."""
        stripped = text.strip()
        if not stripped:
            return ContentKind.GENERIC_LOG

        if stripped.startswith("diff --git ") or ("@@ -" in stripped and "+++ b/" in stripped):
            return ContentKind.GIT_DIFF

        if (stripped.startswith("{") and stripped.endswith("}")) or (stripped.startswith("[") and stripped.endswith("]")):
            return ContentKind.JSON_DATA

        if "Traceback (most recent call last):" in text or re.search(r'File ".*", line \d+', text):
            return ContentKind.TRACEBACK

        if "short test summary info" in text or re.search(r'=+.*(?:passed|failed|errors).*=+', text) or "Running unittests" in text:
            return ContentKind.TEST_RUNNER

        # Check if text looks like python code
        if re.search(r'^(?:import |from |class |def |async def )', stripped, re.MULTILINE):
            return ContentKind.CODE

        return ContentKind.GENERIC_LOG

    def distill(
        self,
        text: str,
        kind: ContentKind | None = None,
        focus_symbols: Sequence[str] | None = None,
        focus_lines: Sequence[int] | None = None,
        max_tokens: int | None = None,
    ) -> DistillationResult:
        """
        Distills raw tool output according to its structure and assigned budget.
        """
        budget = max_tokens or self.default_max_tokens
        detected_kind = kind or self.detect_kind(text)

        if detected_kind == ContentKind.GIT_DIFF:
            distilled = distill_git_diff(text)
        elif detected_kind == ContentKind.JSON_DATA:
            distilled = distill_json(text)
        elif detected_kind == ContentKind.TRACEBACK:
            distilled = distill_traceback(text)
        elif detected_kind == ContentKind.TEST_RUNNER:
            distilled = distill_test_output(text)
        elif detected_kind == ContentKind.CODE:
            distilled = distill_code(text, focus_symbols=focus_symbols, focus_lines=focus_lines)
        else:
            # Generic log truncation with head/tail budget if over
            distilled = self._distill_generic(text, budget)

        # Check if distilled still exceeds token budget
        est_tokens = estimate_tokens(distilled)
        if est_tokens > budget:
            distilled = self._distill_generic(distilled, budget)

        metrics = compute_metrics(text, distilled)
        
        return DistillationResult(
            kind=detected_kind,
            original_tokens=metrics.original_tokens_est,
            distilled_tokens=metrics.distilled_tokens_est,
            saved_tokens=metrics.saved_tokens_est,
            savings_percent=round(metrics.savings_percent, 2),
            distilled_text=distilled,
            metadata={
                "original_chars": metrics.original_chars,
                "distilled_chars": metrics.distilled_chars,
            },
        )

    def _distill_generic(self, text: str, budget: int) -> str:
        lines = text.splitlines()
        if len(lines) <= 40:
            return text
        
        # Retain top 20 and bottom 20 lines with summary gap
        head = lines[:20]
        tail = lines[-20:]
        omitted = len(lines) - 40
        
        return "\n".join(head + [f"\n... [agentsieve: {omitted} lines omitted to stay within token budget] ...\n"] + tail)


# Global singleton instance
def distill_tool_output(text: str, **kwargs: Any) -> DistillationResult:
    return AgentSieve().distill(text, **kwargs)
