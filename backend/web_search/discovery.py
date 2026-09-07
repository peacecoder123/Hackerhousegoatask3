"""
web_search/discovery.py
------------------------
Genuine reverse image search via SerpAPI Google Lens.

Flow:
  1. Upload compressed image to 0x0.st (free temp host) to get a public URL
  2. Query SerpAPI Google Lens with that URL
  3. Download visual match thumbnails locally
  4. Score candidates via Member 1's FaceDetector
  5. Return sorted candidates

Member 2 owns this file.
"""
import os
import uuid
import requests
from PIL import Image

try:
    from serpapi import GoogleSearch
except ImportError:
    from google_search_results import GoogleSearch


def upload_to_public_host(local_path: str) -> str:
    """
    Upload a local image to a public temporary host and return the URL.
    Tries multiple hosts in order; raises RuntimeError if all fail.
    """
    filename = os.path.basename(local_path)

    # ── Host 1: catbox.moe ───────────────────────────────────────────
    try:
        with open(local_path, "rb") as f:
            r = requests.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": (filename, f, "image/jpeg")},
                timeout=30,
            )
        r.raise_for_status()
        url = r.text.strip()
        if url.startswith("http"):
            print(f"[discovery] Uploaded to catbox.moe: {url}")
            return url
    except Exception as e:
        print(f"[discovery] catbox.moe failed: {e}")

    # ── Host 2: transfer.sh ──────────────────────────────────────────
    try:
        with open(local_path, "rb") as f:
            r = requests.put(
                f"https://transfer.sh/{filename}",
                data=f,
                timeout=30,
            )
        r.raise_for_status()
        url = r.text.strip()
        if url.startswith("http"):
            print(f"[discovery] Uploaded to transfer.sh: {url}")
            return url
    except Exception as e:
        print(f"[discovery] transfer.sh failed: {e}")

    # ── Host 3: 0x0.st ──────────────────────────────────────────────
    try:
        with open(local_path, "rb") as f:
            r = requests.post(
                "https://0x0.st",
                files={"file": (filename, f, "image/jpeg")},
                timeout=30,
            )
        r.raise_for_status()
        url = r.text.strip()
        if url.startswith("http"):
            print(f"[discovery] Uploaded to 0x0.st: {url}")
            return url
    except Exception as e:
        print(f"[discovery] 0x0.st failed: {e}")

    raise RuntimeError("All public image hosts failed. Check network connectivity.")


def download_image(url: str, download_dir: str = "candidates") -> str | None:
    """Download a candidate image to disk for feature extraction and hashing."""
    os.makedirs(download_dir, exist_ok=True)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        filepath = os.path.join(download_dir, f"{uuid.uuid4().hex}.jpg")
        with open(filepath, "wb") as f:
            f.write(response.content)
        return filepath
    except Exception as err:
        print(f"Failed to download {url}: {err}")
        return None


def search_by_image(input_image_path: str) -> list[dict]:
    """
    Execute a genuine reverse image search via SerpAPI Google Lens.

    Steps:
      1. Compress image to max 800x800 JPEG
      2. Upload to 0x0.st to get a public URL
      3. Query SerpAPI Google Lens with the public URL
      4. Download + score top visual matches using Member 1's FaceDetector
      5. Return candidates sorted by similarity score
    """
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        raise ValueError("SERPAPI_KEY not found in environment variables.")

    # ── 1. Compress image ────────────────────────────────────────────
    compressed_path = "compressed_input.jpg"
    with Image.open(input_image_path) as img:
        img.thumbnail((800, 800))
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(compressed_path, format="JPEG", quality=85)

    # ── 2. Upload to public host ─────────────────────────────────────
    try:
        public_url = upload_to_public_host(compressed_path)
    except Exception as e:
        raise RuntimeError(f"Failed to upload image for web search: {e}") from e

    # ── 3. SerpAPI Google Lens search ────────────────────────────────
    try:
        search = GoogleSearch({
            "engine": "google_lens",
            "url": public_url,
            "api_key": api_key,
        })
        results = search.get_dict()
        visual_matches = results.get("visual_matches", [])
    except Exception as e:
        print(f"SerpAPI search error: {e}")
        visual_matches = []

    if not visual_matches:
        return []

    # ── 4. Score candidates via Member 1's FaceDetector ─────────────
    # Import here to avoid circular imports at module level
    from face_detection import FaceDetector
    detector = FaceDetector()
    candidates = []

    for match in visual_matches[:5]:
        image_url = (
            match.get("thumbnail")
            or match.get("image")
            or match.get("link", "")
        )
        if not image_url or not image_url.startswith("http"):
            continue

        local_img = download_image(image_url)
        if not local_img:
            continue

        try:
            result = detector.detect_and_encode(local_img)
            score = float(result.get("confidence", 0.75)) if result.get("success") else 0.50
        except Exception:
            score = 0.50

        candidates.append({
            "url": match.get("link", match.get("source", "")),
            "platform": match.get("source", "Web"),
            "title": match.get("title", "Discovered Web Match"),
            "caption": match.get("snippet", ""),
            "author": match.get("source", "Unknown"),
            "timestamp": match.get("date", "Unknown"),
            "score": score,
            "local_path": local_img,
        })

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates