"""web_search/__init__.py"""
from .searcher import search_by_image, SearchMatch
from .scorer import compute_similarity, rank_candidates

__all__ = ["search_by_image", "SearchMatch", "compute_similarity", "rank_candidates"]
