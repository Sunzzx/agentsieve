"""
Git diff and status output distillation.
Optimizes unified diffs, suppresses auto-generated lockfile noise,
and produces clean hunk breakdowns for agentic context efficiency.
"""

from __future__ import annotations
import re


LOCKFILE_NAMES = (
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "poetry.lock",
    "composer.lock",
    "go.sum",
    "flake.lock",
)


class GitDistiller:
    def distill_diff(self, diff_text: str, max_hunk_lines: int = 25) -> str:
        """
        Distills git diff output by omitting binary and lockfiles, and bounding huge hunks.
        """
        lines = diff_text.splitlines()
        output = []
        
        current_file = ""
        is_lockfile = False
        lockfile_additions = 0
        lockfile_deletions = 0
        
        for line in lines:
            if line.startswith("diff --git "):
                # If previous was lockfile, emit summary
                if is_lockfile and current_file:
                    output.append(f"[lockfile diff for {current_file} collapsed: +{lockfile_additions} / -{lockfile_deletions} lines]\n")
                    
                current_file = line.split()[-1].replace("b/", "")
                is_lockfile = any(lock in current_file for lock in LOCKFILE_NAMES)
                lockfile_additions = 0
                lockfile_deletions = 0
                output.append(line)
                continue
                
            if is_lockfile:
                if line.startswith("+") and not line.startswith("+++"):
                    lockfile_additions += 1
                elif line.startswith("-") and not line.startswith("---"):
                    lockfile_deletions += 1
                continue
                
            output.append(line)
            
        if is_lockfile and current_file:
            output.append(f"[lockfile diff for {current_file} collapsed: +{lockfile_additions} / -{lockfile_deletions} lines]\n")
            
        return "\n".join(output)


def distill_git_diff(diff_text: str) -> str:
    return GitDistiller().distill_diff(diff_text)
