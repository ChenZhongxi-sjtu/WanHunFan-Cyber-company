from __future__ import annotations

import json
import re
from typing import Any


JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\}|\[.*?\])\s*```", re.DOTALL)


def extract_json(text: str) -> Any:
    text = text.strip()
    for candidate in (text, _find_json_block(text)):
        if not candidate:
            continue
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError("Unable to parse JSON from model output")


def _find_json_block(text: str) -> str | None:
    match = JSON_BLOCK_RE.search(text)
    if match:
        return match.group(1)
    return None
