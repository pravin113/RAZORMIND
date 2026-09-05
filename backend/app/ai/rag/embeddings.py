from __future__ import annotations

import math
from typing import Sequence

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

# Lightweight, deterministic 128-dim local embedding generator
_VECTORIZER = HashingVectorizer(
    n_features=128,
    norm="l2",
    alternate_sign=True,
    ngram_range=(1, 2),
    lowercase=True,
)


def generate_embedding(text: str) -> list[float]:
    """Generate deterministic L2-normalized 128-dimensional embedding vector locally."""
    if not text or not text.strip():
        return [0.0] * 128
    dense = _VECTORIZER.transform([text.strip()]).toarray()[0]
    return [float(x) for x in dense]


def cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    arr_a = np.asarray(vec_a, dtype=np.float32)
    arr_b = np.asarray(vec_b, dtype=np.float32)
    norm_a = np.linalg.norm(arr_a)
    norm_b = np.linalg.norm(arr_b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    sim = float(np.dot(arr_a, arr_b) / (norm_a * norm_b))
    return max(0.0, min(1.0, (sim + 1.0) / 2.0))  # Scale from [-1, 1] to [0, 1]
