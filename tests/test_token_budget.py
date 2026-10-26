import pytest
from agentsieve.token_budget import estimate_tokens, compute_metrics

def test_estimate_tokens_empty():
    assert estimate_tokens("") == 0

def test_estimate_tokens_sample():
    text = "def calculate_matrix_weights(alpha: float, beta: float) -> list[float]:\n    return [alpha * i + beta for i in range(10)]"
    tokens = estimate_tokens(text)
    assert tokens > 10
    assert tokens < 100

def test_compute_metrics():
    orig = "a" * 1000
    dist = "a" * 200
    metrics = compute_metrics(orig, dist)
    assert metrics.original_chars == 1000
    assert metrics.distilled_chars == 200
    assert metrics.savings_percent > 70.0
    assert metrics.saved_tokens_est > 0
