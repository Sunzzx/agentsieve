"""
Test runner output distillation.
Extracts failing tests, failure assertions, captured error logs, and overall execution tallies
from pytest, cargo test, and npm test outputs while discarding thousands of lines of pass noise.
"""

from __future__ import annotations
import re


class TestRunnerDistiller:
    """
    Distills test runner logs to actionable failure reports.
    """

    def distill_pytest(self, text: str) -> str:
        lines = text.splitlines()
        output = []
        
        # Extract summary line (e.g., "= 1 failed, 12 passed in 1.45s =")
        summary_pattern = re.compile(r'=+\s*(.*(?:passed|failed|error).*)\s*=+')
        failure_header_pattern = re.compile(r'_+\s*(test_[a-zA-Z0-9_\[\]\-]+|Test[a-zA-Z0-9_]+::\S+)\s*_+')
        
        in_failure_section = False
        in_short_test_summary = False
        failure_blocks: list[list[str]] = []
        current_block: list[str] = []
        summary_line = ""
        short_summary_lines: list[str] = []

        for line in lines:
            # Check for failure block header
            m_fail = failure_header_pattern.match(line)
            if m_fail:
                if current_block:
                    failure_blocks.append(current_block)
                current_block = [f"[FAILING TEST] {m_fail.group(1)}"]
                in_failure_section = True
                continue

            # Check for short test summary info
            if "=== short test summary info ===" in line:
                in_failure_section = False
                in_short_test_summary = True
                if current_block:
                    failure_blocks.append(current_block)
                    current_block = []
                continue

            m_sum = summary_pattern.match(line)
            if m_sum and any(w in line for w in ("passed", "failed", "errors", "skipped")):
                summary_line = m_sum.group(1)
                in_failure_section = False
                in_short_test_summary = False
                continue

            if in_short_test_summary:
                if line.startswith("FAILED ") or line.startswith("ERROR "):
                    short_summary_lines.append(line)
                continue

            if in_failure_section:
                # Filter out pure separator lines
                if line.startswith("===") or line.startswith("------ Captured"):
                    if line.startswith("------ Captured"):
                        current_block.append(f"  {line}")
                    continue
                current_block.append(f"  {line}")

        if current_block:
            failure_blocks.append(current_block)

        if not failure_blocks and not short_summary_lines and not summary_line:
            return text  # Not recognized or all passed without standard format

        result = ["=== [agentsieve: Test Runner Distillation] ==="]
        if summary_line:
            result.append(f"STATUS: {summary_line}")

        if short_summary_lines:
            result.append("\nFAILURES SUMMARY:")
            for s in short_summary_lines:
                result.append(f"  * {s}")

        if failure_blocks:
            result.append("\nFAILURE DETAILS:")
            for block in failure_blocks:
                result.append("\n".join(block))
                result.append("-" * 40)

        if not failure_blocks and not short_summary_lines:
            result.append("All tests passed successfully (pass logs collapsed).")

        return "\n".join(result)

    def distill_cargo_test(self, text: str) -> str:
        """Distills cargo test / rust test output."""
        lines = text.splitlines()
        output = ["=== [agentsieve: Cargo Test Distillation] ==="]
        in_failures = False
        captured_failures = []
        summary_lines = []
        
        for line in lines:
            if line.startswith("failures:"):
                in_failures = True
                continue
            if in_failures and line.startswith("test result:"):
                in_failures = False
                summary_lines.append(line)
                continue
            if in_failures:
                captured_failures.append(line)
            elif line.startswith("test result:"):
                summary_lines.append(line)
                
        if summary_lines:
            output.extend(summary_lines)
        if captured_failures:
            output.append("\nFAILURES:")
            output.extend(captured_failures)
            
        return "\n".join(output) if (summary_lines or captured_failures) else text

    def distill(self, text: str) -> str:
        if "pytest" in text or "short test summary info" in text or re.search(r'=+ (?:passed|failed).* =+', text):
            return self.distill_pytest(text)
        if "Running unittests" in text or "test result:" in text:
            return self.distill_cargo_test(text)
        return text


def distill_test_output(text: str) -> str:
    return TestRunnerDistiller().distill(text)
