"""
web_search/searcher.py
----------------------
Step 2 of the FaceChain Verify pipeline.

Performs a reverse image search to find matching social media content.

Member 2 owns this file.
"""

from __future__ import annotations
import os
from typing import TypedDict


class SearchMatch(TypedDict):
    url: str             # Direct link to the matching post/page
    platform: str        # e.g. "Instagram", "Reddit", "Personal blog"
    title: str           # Page or post title
    thumbnail_url: str   # URL of the matching thumbnail image
    score: float         # Visual similarity score (0–1)


def search_by_image(image_path: str) -> list[SearchMatch]:
    """
    Perform a reverse image search and return ranked candidate matches.

    Args:
        image_path: Path to the face image to search for.

    Returns:
        A list of SearchMatch dicts, ordered by score descending.
        The first item is the best (most visually similar) match.

    Raises:
        FileNotFoundError: If the image path does not exist.
        RuntimeError: If the search API call fails.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        raise RuntimeError(
            "SERPAPI_KEY environment variable is not set. "
            "Add it to your .env file."
        )

    # TODO (Member 2): Replace this stub with a real SerpAPI / Google Vision call.
    #
    # Example using SerpAPI Google Lens:
    #   from serpapi import GoogleSearch
    #   params = {
    #       "engine": "google_lens",
    #       "url": <upload image to a public URL first, or use base64>,
    #       "api_key": api_key,
    #   }
    #   results = GoogleSearch(params).get_dict()
    #   visual_matches = results.get("visual_matches", [])
    #   ...parse and score visual_matches into SearchMatch dicts...

    raise NotImplementedError(
        "search_by_image() is not yet implemented. "
        "See the TODO comment above for guidance."
    )
