import pytest
from agentsieve.ast_pruner import distill_code, ASTCodeDistiller

SAMPLE_CODE = """import os
import sys

class Engine:
    def __init__(self, mode: str = 'fast'):
        self.mode = mode
        self.state = {}
        self._initialize_buffers()

    def _initialize_buffers(self):
        for i in range(100):
            self.state[i] = [0] * 50
        print('Buffers initialized')

    def execute(self, payload: dict) -> dict:
        step1 = self._transform(payload)
        step2 = self._compute(step1)
        return {'status': 'ok', 'result': step2}

def helper_func(x: int) -> int:
    val = x * 2
    return val + 1
"""

def test_ast_distill_collapses_unfocused():
    distilled = distill_code(SAMPLE_CODE)
    assert "class Engine:" in distilled
    assert "def execute(self, payload: dict) -> dict:" in distilled
    assert "lines collapsed" in distilled
    assert "step1 = self._transform(payload)" not in distilled

def test_ast_distill_with_focus_symbol():
    distilled = distill_code(SAMPLE_CODE, focus_symbols=["execute"])
    assert "step1 = self._transform(payload)" in distilled
    assert "step2 = self._compute(step1)" in distilled
    assert "self.state[i] = [0] * 50" not in distilled

def test_ast_distill_syntax_error_fallback():
    broken_code = "def broken(a, b:\n    x = 1\n    return x"
    distilled = distill_code(broken_code)
    assert "def broken" in distilled
