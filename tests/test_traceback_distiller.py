import pytest
from agentsieve.traceback_distiller import distill_traceback, TracebackDistiller

MOCK_PYTHON_TB = """Traceback (most recent call last):
  File "/Users/ayu/Developer/agentsieve/run.py", line 12, in <module>
    main()
  File "/Users/ayu/Developer/agentsieve/run.py", line 8, in main
    execute_pipeline()
  File "/opt/anaconda3/lib/python3.13/site-packages/click/core.py", line 1157, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
  File "/opt/anaconda3/lib/python3.13/site-packages/click/core.py", line 1434, in invoke
    return ctx.invoke(self.callback, **ctx.params)
  File "/Users/ayu/Developer/agentsieve/agentsieve/core.py", line 55, in execute_pipeline
    raise ValueError("Invalid budget specified: -500")
ValueError: Invalid budget specified: -500
"""

def test_python_traceback_distill():
    distilled = distill_traceback(MOCK_PYTHON_TB)
    assert "ValueError: Invalid budget specified: -500" in distilled
    assert "run.py:12 in <module>" in distilled
    assert "core.py:55 in execute_pipeline" in distilled
    assert "framework/library frames hidden" in distilled
    assert "click/core.py" not in distilled

def test_node_traceback_distill():
    node_tb = """Error: Database connection timeout
    at Connection.connect (/app/src/db.ts:45:12)
    at runQuery (/app/node_modules/pg/lib/client.js:100:5)
    at handleRequest (/app/src/server.ts:18:9)
"""
    distilled = distill_traceback(node_tb)
    assert "Error: Database connection timeout" in distilled
    assert "/app/src/db.ts:45 in Connection.connect" in distilled
    assert "/app/src/server.ts:18 in handleRequest" in distilled
    assert "internal/node_modules frames hidden" in distilled
