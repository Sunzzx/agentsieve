"""
AgentSieve: Zero-LLM, high-speed semantic & AST-aware tool output distiller for autonomous coding agents.
"""

from agentsieve.core import (
    AgentSieve,
    ContentKind,
    DistillationResult,
    distill_tool_output,
)
from agentsieve.ast_pruner import distill_code, ASTCodeDistiller
from agentsieve.traceback_distiller import distill_traceback, TracebackDistiller
from agentsieve.test_runner_distiller import distill_test_output, TestRunnerDistiller
from agentsieve.json_distiller import distill_json, JSONDistiller
from agentsieve.git_distiller import distill_git_diff, GitDistiller
from agentsieve.token_budget import estimate_tokens, compute_metrics, TokenMetrics

__version__ = "0.1.0"
__all__ = [
    "AgentSieve",
    "ContentKind",
    "DistillationResult",
    "distill_tool_output",
    "distill_code",
    "ASTCodeDistiller",
    "distill_traceback",
    "TracebackDistiller",
    "distill_test_output",
    "TestRunnerDistiller",
    "distill_json",
    "JSONDistiller",
    "distill_git_diff",
    "GitDistiller",
    "estimate_tokens",
    "compute_metrics",
    "TokenMetrics",
]
