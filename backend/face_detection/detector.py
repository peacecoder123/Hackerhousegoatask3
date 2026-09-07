import os
import cv2
import numpy as np
from deepface import DeepFace
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger("face_detector")

class FaceDetector:
    def __init__(self, model_name: str = "Facenet"):
        self.model_name = model_name

    def detect_and_encode(self, image_path: str) -> Dict[str, Any]:
        if not os.path.exists(image_path):
            logger.error(f"Image path does not exist: {image_path}")
            return {"success": False, "error": f"File not found: {image_path}"}

        try:
            embedding_objs = DeepFace.represent(
                img_path=image_path,
                model_name=self.model_name,
                enforce_detection=True
            )

            if not embedding_objs:
                logger.warning(f"No face detected in {image_path}")
                return {
                    "success": False,
                    "error": "No face detected in the provided image scan.",
                    "faces_found": 0
                }

            primary_embedding = embedding_objs[0]["embedding"]
            facial_area = embedding_objs[0]["facial_area"]

            logger.info(f"Successfully detected {len(embedding_objs)} face(s) in {image_path}")

            return {
                "success": True,
                "faces_found": len(embedding_objs),
                "facial_area": facial_area,
                "bbox": [facial_area["x"], facial_area["y"], facial_area["w"], facial_area["h"]],  # Added for pipeline compatibility
                "primary_encoding": primary_embedding,
                "confidence": 0.99,
                "image_path": image_path
            }

        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            return {"success": False, "error": str(e)}