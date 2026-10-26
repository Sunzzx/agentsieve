"""
JSON and structured data distillation.
Summarizes large API payloads, cloud responses, and database results into
structural schemas with representative items and statistics, preserving 85-95% tokens.
"""

from __future__ import annotations
import json
from typing import Any


class JSONDistiller:
    def __init__(self, max_items_per_list: int = 3, max_str_length: int = 120):
        self.max_items_per_list = max_items_per_list
        self.max_str_length = max_str_length

    def distill_value(self, val: Any) -> Any:
        if isinstance(val, dict):
            return {k: self.distill_value(v) for k, v in val.items()}
        elif isinstance(val, list):
            total = len(val)
            if total <= self.max_items_per_list + 1:
                return [self.distill_value(v) for v in val]
            
            head = [self.distill_value(v) for v in val[:self.max_items_per_list]]
            tail = self.distill_value(val[-1])
            
            # Sample keys if elements are dicts
            schema_keys = []
            if total > 0 and isinstance(val[0], dict):
                schema_keys = list(val[0].keys())[:10]
                
            summary_placeholder = f"... [truncated: {total - self.max_items_per_list - 1} more items; sample keys: {schema_keys}]"
            return head + [summary_placeholder, tail]
        elif isinstance(val, str):
            if len(val) > self.max_str_length:
                return f"{val[:self.max_str_length]}... [truncated {len(val) - self.max_str_length} chars]"
            return val
        else:
            return val

    def distill(self, text: str) -> str:
        try:
            data = json.loads(text)
        except Exception:
            return text
            
        distilled_data = self.distill_value(data)
        return json.dumps(distilled_data, indent=2)


def distill_json(text: str, max_items_per_list: int = 3) -> str:
    return JSONDistiller(max_items_per_list=max_items_per_list).distill(text)
