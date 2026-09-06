# `web_search/` — Reverse Image Search & Social Post Retrieval

**Owner: Member 2 (Web / Social Media Search Engineer)**

## Responsibility

This module is the second step in the pipeline:

1. Take the face embedding (from `face_detection`) and the source image
2. Perform a reverse image search against the public web
3. Find at least one real, matching social media post
4. Score and rank candidates by visual similarity
5. Return the best match's metadata (URL, platform, title, image URL)

## Files

| File | Purpose |
|------|---------|
| `searcher.py` | Core reverse image search logic |
| `scorer.py` | Visual similarity scoring & candidate ranking |
| `README.md` | This file |

## Recommended Approach

- **SerpAPI** (Google Lens / Reverse Image Search) — most reliable, returns structured results  
  ```bash
  pip install google-search-results
  ```
- **Google Vision API** — SafeSearch + web detection in one call  
- **PimEyes** — specialized face search (rate-limited on free tier)

## Usage

```python
from web_search.searcher import search_by_image

matches = search_by_image(image_path="path/to/face.jpg")
# matches = [{ "url": "...", "platform": "Instagram", "title": "...", "score": 0.942 }, ...]

best = matches[0]
```

## Output Contract

```json
[
  {
    "url": "https://www.instagram.com/p/...",
    "platform": "Instagram",
    "title": "A quiet portrait from the coast",
    "thumbnail_url": "https://...",
    "score": 0.942
  }
]
```

## API Keys Required

```env
SERPAPI_KEY=your_serpapi_key_here
```

## Known Limitations

- SerpAPI free tier: ~100 searches/month
- Private or deleted social media posts won't appear
- Results vary by image quality and face visibility
