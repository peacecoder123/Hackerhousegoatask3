"""
face_detection/detector.py
--------------------------
Step 1 of the FaceChain Verify pipeline.

Detects a face in the input image and returns a 128-d embedding vector.

Member 1 owns this file.
"""

from __future__ import annotations
import os
from typing import TypedDict


class FaceResult(TypedDict):
    embedding: list[float]   # 128-dimensional face encoding
    confidence: float        # Detection confidence score (0–1)
    bbox: list[int]          # Bounding box [x, y, width, height]


def encode_face(image_path: str) -> FaceResult:
    """
    Detect and encode the primary face in the given image.

    Args:
        image_path: Absolute or relative path to a JPG/PNG/WEBP file.

    Returns:
        A FaceResult dict with embedding, confidence, and bounding box.

    Raises:
        FileNotFoundError: If the image path does not exist.
        ValueError: If no face is detected in the image.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    # TODO (Member 1): Replace this stub with a real implementation.
    # Recommended: `import face_recognition` or `from deepface import DeepFace`
    #
    # Example using face_recognition:
    #   import face_recognition
    #   image = face_recognition.load_image_file(image_path)
    #   locations = face_recognition.face_locations(image)
    #   encodings = face_recognition.face_encodings(image, locations)
    #   if not encodings:
    #       raise ValueError("No face detected in the image.")
    #   top, right, bottom, left = locations[0]
    #   return {
    #       "embedding": encodings[0].tolist(),
    #       "confidence": 0.93,   # face_recognition doesn't return confidence natively
    #       "bbox": [left, top, right - left, bottom - top],
    #   }

    raise NotImplementedError(
        "encode_face() is not yet implemented. "
        "See the TODO comment above for guidance."
    )
