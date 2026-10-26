import json
import pytest
from agentsieve.json_distiller import distill_json

def test_json_distill_truncates_long_lists():
    items = [{"id": i, "name": f"Item {i}", "desc": "test"} for i in range(100)]
    payload = json.dumps({"status": "ok", "items": items})
    
    distilled = distill_json(payload, max_items_per_list=2)
    parsed = json.loads(distilled)
    
    assert parsed["status"] == "ok"
    assert len(parsed["items"]) == 4
    assert "truncated: 97 more items" in str(parsed["items"][2])

def test_json_distill_truncates_huge_strings():
    huge_str = "A" * 500
    payload = json.dumps({"data": huge_str})
    distilled = distill_json(payload)
    parsed = json.loads(distilled)
    assert "truncated" in parsed["data"]
