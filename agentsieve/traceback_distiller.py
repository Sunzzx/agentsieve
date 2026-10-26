"""
Traceback and error distillation.
Filters noise, standard library/virtualenv frames, and redundant spans from error logs,
preserving only actionable root-cause locations, lines, and messages.
"""

from __future__ import annotations
import re
from dataclasses import dataclass


@dataclass
class FrameInfo:
    file_path: str
    line_num: int
    func_name: str
    code_line: str
    is_framework: bool


class TracebackDistiller:
    """
    Distills multi-language stack traces (Python, Node.js, Rust/Cargo, Go).
    """

    # Framework and third-party markers to collapse
    FRAMEWORK_PATTERNS = (
        "site-packages",
        "dist-packages",
        "/lib/python",
        "node_modules",
        "/rustc/",
        "/.cargo/registry",
        "/go/pkg/mod",
    )

    def distill_python_traceback(self, text: str) -> str:
        """
        Extracts the essential user-code frames and root cause exception from a Python traceback.
        """
        lines = text.splitlines()
        output_lines: list[str] = []
        
        frame_pattern = re.compile(r'\s*File "([^"]+)", line (\d+), in (.*)')
        exception_pattern = re.compile(r'^([a-zA-Z_][a-zA-Z0-9_.]*(?:Error|Exception|Warning|Exit|Interrupt|Fault|Signal)|AssertionError|SystemExit):\s*(.*)$')
        
        i = 0
        n = len(lines)
        hidden_framework_count = 0
        
        while i < n:
            line = lines[i]
            match = frame_pattern.match(line)
            if match:
                file_path = match.group(1)
                line_num = match.group(2)
                func_name = match.group(3)
                
                # Next line usually contains the code snippet
                code_snippet = ""
                if i + 1 < n and not frame_pattern.match(lines[i + 1]) and lines[i + 1].startswith("    "):
                    code_snippet = lines[i + 1].strip()
                    i += 1
                
                is_framework = any(pat in file_path for pat in self.FRAMEWORK_PATTERNS)
                
                if is_framework:
                    hidden_framework_count += 1
                else:
                    if hidden_framework_count > 0:
                        output_lines.append(f"    [... {hidden_framework_count} framework/library frames hidden ...]")
                        hidden_framework_count = 0
                    output_lines.append(f"  -> {file_path}:{line_num} in {func_name}")
                    if code_snippet:
                        output_lines.append(f"     | {code_snippet}")
            else:
                # Check for root exception or general message
                if hidden_framework_count > 0 and (line.startswith("Traceback") or line.strip()):
                    output_lines.append(f"    [... {hidden_framework_count} framework/library frames hidden ...]")
                    hidden_framework_count = 0
                
                exc_match = exception_pattern.match(line.strip())
                if exc_match or line.startswith("Traceback (most recent call last):") or "Error:" in line:
                    output_lines.append(line)
                elif not line.strip():
                    output_lines.append(line)
                else:
                    # Keep high-signal lines (assertions, causes)
                    if any(kw in line for kw in ("AssertionError", "FAILED", "Error", "Exception", "Caused by", "During handling of the above")):
                        output_lines.append(line)
            i += 1
            
        if hidden_framework_count > 0:
            output_lines.append(f"    [... {hidden_framework_count} framework/library frames hidden ...]")
            
        return "\n".join(output_lines) if output_lines else text

    def distill_node_traceback(self, text: str) -> str:
        """Distills Node.js / JavaScript / TypeScript stack traces."""
        lines = text.splitlines()
        output = []
        node_frame = re.compile(r'\s*at (?:(.+) )?\((.+):(\d+):(\d+)\)|\s*at (.+):(\d+):(\d+)')
        hidden = 0
        
        for line in lines:
            m = node_frame.match(line)
            if m:
                loc = m.group(2) or m.group(5) or ""
                fn = m.group(1) or "<anonymous>"
                ln = m.group(3) or m.group(6) or "?"
                
                if "node_modules" in loc or "node:internal" in loc:
                    hidden += 1
                else:
                    if hidden > 0:
                        output.append(f"    [... {hidden} internal/node_modules frames hidden ...]")
                        hidden = 0
                    output.append(f"  -> {loc}:{ln} in {fn}")
            else:
                if hidden > 0:
                    output.append(f"    [... {hidden} internal/node_modules frames hidden ...]")
                    hidden = 0
                output.append(line)
                
        if hidden > 0:
            output.append(f"    [... {hidden} internal/node_modules frames hidden ...]")
        return "\n".join(output)

    def distill(self, text: str) -> str:
        if "Traceback (most recent call last):" in text or re.search(r'File ".*", line \d+', text):
            return self.distill_python_traceback(text)
        if "    at " in text and ("Error:" in text or "Exception" in text):
            return self.distill_node_traceback(text)
        return text


def distill_traceback(text: str) -> str:
    return TracebackDistiller().distill(text)
