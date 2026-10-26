import pytest
from click.testing import CliRunner
from agentsieve.cli import cli

def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output

def test_cli_distill_stdin():
    runner = CliRunner()
    result = runner.invoke(cli, ["distill", "--no-stats"], input='{"items": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}')
    assert result.exit_code == 0
    assert "truncated" in result.output

def test_cli_inspect(tmp_path):
    p = tmp_path / "test.json"
    p.write_text('{"key": "val"}')
    runner = CliRunner()
    result = runner.invoke(cli, ["inspect", str(p)])
    assert result.exit_code == 0
    assert "AgentSieve Analysis" in result.output
