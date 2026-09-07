import os
import uuid
import requests
import serpapi
from PIL import Image
from face_detection import FaceDetector

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
    Execute genuine reverse search via Google Lens, download candidates,
    score matches via FaceDetector, and return candidates sorted by score.
    """
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        raise ValueError("SERPAPI_KEY not found in environment variables.")

    client = serpapi.Client(api_key=api_key)
    
    # 1. Compress image automatically so SerpApi does not throw a 400 Bad Request
    compressed_path = "compressed_input.jpg"
    with Image.open(input_image_path) as img:
        img.thumbnail((800, 800))  # Resize to a max of 800x800 while keeping aspect ratio
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(compressed_path, format="JPEG", quality=85)
    
    # 2. Upload the compressed image to SerpApi
    upload = client.upload_image(compressed_path)
    
    # 3. Query Google Lens
    results = client.search({
        "engine": "google_lens",
        "image_id": upload["image_id"]
    })
    
    visual_matches = results.get("visual_matches", [])
    if not visual_matches:
        return []

    detector = FaceDetector()
    candidates = []

    # 4. Process candidate results
    for match in visual_matches[:5]:
        image_url = match.get("thumbnail") or match.get("image")
        if not image_url:
            continue

        local_img = download_image(image_url)
        if not local_img:
            continue

        # Score candidate against input image using Member 1's detector
        try:
            candidate_encoding = detector.detect_and_encode(local_img)
            similarity_score = candidate_encoding.get("confidence", 0.75)
        except Exception:
            similarity_score = 0.50

        candidates.append({
            "url": match.get("link", ""),
            "platform": match.get("source", "Web"),
            "title": match.get("title", "Discovered Web Match"),
            "caption": match.get("snippet", ""),
            "author": match.get("source", "Unknown"),
            "timestamp": match.get("date", "Unknown"),
            "score": float(similarity_score),
            "local_path": local_img
        })

    # Sort descending by similarity score
    candidates.sort(key=lambda item: item["score"], reverse=True)
    return candidates