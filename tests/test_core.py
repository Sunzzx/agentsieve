import pytest
from agentsieve.core import AgentSieve, ContentKind, distill_tool_output

def test_detect_kind():
    sieve = AgentSieve()
    assert sieve.detect_kind("diff --git a/foo b/foo") == ContentKind.GIT_DIFF
    assert sieve.detect_kind('{"key": "val"}') == ContentKind.JSON_DATA
    assert sieve.detect_kind("=== 1 failed, 2 passed in 0.1s ===") == ContentKind.TEST_RUNNER
    assert sieve.detect_kind("def foo():\n    return 42") == ContentKind.CODE
    assert sieve.detect_kind("Server started on port 8080") == ContentKind.GENERIC_LOG

def test_distill_tool_output_end_to_end():
    huge_log = "\n".join([f"INFO Task #{i}" for i in range(200)])
    res = distill_tool_output(huge_log, max_tokens=100)
    assert res.kind == ContentKind.GENERIC_LOG
    assert res.original_tokens > res.distilled_tokens
    assert res.savings_percent > 50
    assert "lines omitted" in res.distilled_text
