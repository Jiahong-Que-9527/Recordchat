"""In-process lexical (BM25-lite) index for hybrid retrieval (#29).

Dense vectors miss exact config keys, endpoint paths, and error strings.
This index ranks chunks by token overlap so those lexical hits can join the
candidate pool via reciprocal-rank fusion.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Callable

from app.models.source import Chunk

# Keep path-like and dotted tokens (e.g. /subscriptions, docker-compose, http-client.env).
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[._/-][a-z0-9]+)*", re.IGNORECASE)

# BM25 parameters
_K1 = 1.2
_B = 0.75


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text or "")]


class LexicalIndex:
    """Corpus-local BM25 index keyed by chunk_id."""

    def __init__(self) -> None:
        self._docs: dict[str, Chunk] = {}
        self._tf: dict[str, Counter[str]] = {}
        self._df: Counter[str] = Counter()
        self._doc_len: dict[str, int] = {}
        self._avgdl = 0.0

    def clear(self) -> None:
        self._docs.clear()
        self._tf.clear()
        self._df.clear()
        self._doc_len.clear()
        self._avgdl = 0.0

    def add(self, chunks: list[Chunk]) -> None:
        for chunk in chunks:
            self._add_one(chunk)
        self._recompute_avgdl()

    def _add_one(self, chunk: Chunk) -> None:
        # Replace if re-upserted.
        if chunk.chunk_id in self._docs:
            self._remove_stats(chunk.chunk_id)
        tokens = tokenize(chunk.content)
        if chunk.metadata.section_title:
            tokens.extend(tokenize(chunk.metadata.section_title))
        if chunk.metadata.entity:
            tokens.extend(tokenize(chunk.metadata.entity))
        if chunk.metadata.source_name:
            tokens.extend(tokenize(chunk.metadata.source_name))
        tf: Counter[str] = Counter(tokens)
        self._docs[chunk.chunk_id] = chunk
        self._tf[chunk.chunk_id] = tf
        self._doc_len[chunk.chunk_id] = max(len(tokens), 1)
        for term in tf:
            self._df[term] += 1

    def _remove_stats(self, chunk_id: str) -> None:
        tf = self._tf.pop(chunk_id, None)
        self._doc_len.pop(chunk_id, None)
        self._docs.pop(chunk_id, None)
        if not tf:
            return
        for term in tf:
            self._df[term] -= 1
            if self._df[term] <= 0:
                del self._df[term]

    def _recompute_avgdl(self) -> None:
        if not self._doc_len:
            self._avgdl = 0.0
            return
        self._avgdl = sum(self._doc_len.values()) / len(self._doc_len)

    def search(
        self,
        query: str,
        top_k: int,
        *,
        predicate: Callable[[Chunk], bool] | None = None,
    ) -> list[Chunk]:
        if top_k <= 0 or not self._docs:
            return []
        q_terms = tokenize(query)
        if not q_terms:
            return []

        n = len(self._docs)
        avgdl = self._avgdl or 1.0
        scores: list[tuple[float, str]] = []
        for chunk_id, tf in self._tf.items():
            chunk = self._docs[chunk_id]
            if predicate is not None and not predicate(chunk):
                continue
            score = 0.0
            dl = self._doc_len[chunk_id]
            for term in q_terms:
                freq = tf.get(term, 0)
                if not freq:
                    continue
                df = self._df.get(term, 0)
                idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
                denom = freq + _K1 * (1 - _B + _B * dl / avgdl)
                score += idf * (freq * (_K1 + 1)) / denom
            if score > 0:
                scores.append((score, chunk_id))

        scores.sort(key=lambda item: item[0], reverse=True)
        return [self._docs[chunk_id] for _, chunk_id in scores[:top_k]]


def reciprocal_rank_fuse(
    *ranked_lists: list[Chunk],
    k: int = 60,
    limit: int | None = None,
) -> list[Chunk]:
    """Merge ranked candidate lists with reciprocal rank fusion."""
    scores: dict[str, float] = {}
    by_id: dict[str, Chunk] = {}
    for ranked in ranked_lists:
        for rank, chunk in enumerate(ranked):
            scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + 1.0 / (k + rank + 1)
            by_id[chunk.chunk_id] = chunk
    ordered = sorted(scores, key=scores.get, reverse=True)  # type: ignore[arg-type]
    if limit is not None:
        ordered = ordered[:limit]
    return [by_id[chunk_id] for chunk_id in ordered]
