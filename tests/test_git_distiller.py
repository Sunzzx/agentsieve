import pytest
from agentsieve.git_distiller import distill_git_diff

MOCK_GIT_DIFF = """diff --git a/package-lock.json b/package-lock.json
index 12345..67890 100644
--- a/package-lock.json
+++ b/package-lock.json
@@ -1,5 +1,6 @@
+    "version": "1.0.1",
-    "version": "1.0.0",
+    "integrity": "sha512-abc",
diff --git a/src/index.ts b/src/index.ts
index abcde..fghij 100644
--- a/src/index.ts
+++ b/src/index.ts
@@ -10,3 +10,4 @@
 export function greet() {
-    return "Hello";
+    return "Hello, world!";
 }
"""

def test_git_diff_collapses_lockfile():
    distilled = distill_git_diff(MOCK_GIT_DIFF)
    assert "lockfile diff for package-lock.json collapsed" in distilled
    assert "export function greet()" in distilled
    assert '+    return "Hello, world!";' in distilled
