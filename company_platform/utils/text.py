from __future__ import annotations

import re


WORD_SPLIT_RE = re.compile(r"[\s,;:|/()\[\]{}<>_+\-.]+")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def split_keywords(text: str) -> list[str]:
    normalized = normalize_text(text)
    parts = [part for part in WORD_SPLIT_RE.split(normalized) if len(part) >= 2]
    return list(dict.fromkeys(parts))


def keyword_score(query: str, candidates: list[str]) -> tuple[float, list[str]]:
    normalized_query = normalize_text(query)
    hits: list[str] = []
    score = 0.0
    for keyword in candidates:
        normalized_keyword = normalize_text(keyword)
        if not normalized_keyword:
            continue
        if normalized_keyword in normalized_query:
            hits.append(keyword)
            score += max(1.0, min(len(normalized_keyword) / 2.0, 4.0))
    return score, hits


def truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."
