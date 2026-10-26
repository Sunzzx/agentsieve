import pytest
from agentsieve.test_runner_distiller import distill_test_output, TestRunnerDistiller

MOCK_PYTEST_OUTPUT = """============================= test session starts ==============================
rootdir: /Users/ayu/Developer/project
collected 5 items

tests/test_auth.py .                                                     [ 20%]
tests/test_auth.py .                                                     [ 40%]
tests/test_core.py F                                                     [ 60%]
tests/test_core.py .                                                     [ 80%]
tests/test_core.py .                                                     [100%]

=================================== FAILURES ===================================
__________________________________ test_auth ___________________________________

    def test_auth():
>       assert authenticate("admin", "wrong") == True
E       AssertionError: assert False == True

tests/test_core.py:28: AssertionError
=========================== short test summary info ============================
FAILED tests/test_core.py::test_auth - AssertionError: assert False == True
========================= 1 failed, 4 passed in 0.35s ==========================
"""

def test_pytest_distiller():
    distilled = distill_test_output(MOCK_PYTEST_OUTPUT)
    assert "=== [agentsieve: Test Runner Distillation] ===" in distilled
    assert "1 failed, 4 passed in 0.35s" in distilled
    assert "FAILED tests/test_core.py::test_auth" in distilled
    assert "AssertionError: assert False == True" in distilled
    assert "[ 20%]" not in distilled
    assert "tests/test_auth.py ." not in distilled

def test_cargo_test_distiller():
    cargo_output = """running 3 tests
test tests::test_success ... ok
test tests::test_parse ... ok
test tests::test_panic ... FAILED

failures:

---- tests::test_panic stdout ----
thread 'tests::test_panic' panicked at src/lib.rs:45:9:
assertion `left == right` failed
  left: 10
 right: 20

test result: FAILED. 2 passed; 1 failed; 0 ignored; 0 measured; 0 filtered out
"""
    distilled = distill_test_output(cargo_output)
    assert "Cargo Test Distillation" in distilled
    assert "test result: FAILED. 2 passed; 1 failed" in distilled
    assert "panicked at src/lib.rs:45:9" in distilled
