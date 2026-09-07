import os
from serpapi import GoogleSearch
from utils.logger import get_logger

logger = get_logger("web_search")

def search_by_image(image_path: str) -> list:
    api_key = os.getenv("SERPAPI_KEY")
    
    # Fallback mock for testing/demo if API key isn't configured
    if not api_key or api_key == "your_actual_serpapi_key_here":
        logger.warning("SERPAPI_KEY not found. Returning mock search match for pipeline demonstration.")
        return [{
            "title": "Matching Profile Post",
            "link": "https://instagram.com/p/sample123",
            "snippet": "Verified social media post matching face scan.",
            "source": "Instagram"
        }]

    # Real SerpAPI reverse image search call
    params = {
        "engine": "google_reverse_image",
        "image_url": image_path, # Or upload to a temporary host if SerpAPI requires a public URL
        "api_key": api_key
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        inline_images = results.get("inline_images", [])
        
        matches = []
        for img in inline_images:
            matches.append({
                "title": img.get("title", "Image Match"),
                "link": img.get("link", ""),
                "source": img.get("source", "Web Search")
            })
        return matches
    except Exception as e:
        logger.error(f"SerpAPI search failed: {str(e)}")
        raise RuntimeError(f"Web search error: {str(e)}")