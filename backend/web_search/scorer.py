"""
web_search/scorer.py
--------------------
Visual similarity scoring and candidate ranking helpers.

Member 2 owns this file.
"""

from __future__ import annotations
import hashlib


def compute_similarity(embedding_a: list[float], embedding_b: list[float]) -> float:
    """
    Compute cosine similarity between two face embeddings.

    Args:
        embedding_a: First 128-d face embedding vector.
        embedding_b: Second 128-d face embedding vector.

    Returns:
        Cosine similarity score in range [0, 1]. Higher = more similar.
    """
    # TODO (Member 2): Implement cosine similarity.
    #
    # import numpy as np
    # a = np.array(embedding_a)
    # b = np.array(embedding_b)
    # return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    raise NotImplementedError("compute_similarity() is not yet implemented.")


def rank_candidates(candidates: list[dict]) -> list[dict]:
    """
    Sort a list of candidate matches by score descending.

    Args:
        candidates: List of dicts each containing at minimum a 'score' key.

    Returns:
        The same list sorted by score descending (best match first).
    """
    return sorted(candidates, key=lambda c: c.get("score", 0), reverse=True)
