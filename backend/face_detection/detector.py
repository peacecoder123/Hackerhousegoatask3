import os
import cv2
import numpy as np
from deepface import DeepFace
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger("face_detector")

class FaceDetector:
    def __init__(self, model_name: str = "Facenet"):
        """
        Available models: 'VGG-Face', 'Facenet' (128-d), 'Facenet512', 'OpenFace', 'DeepFace'
        """
        self.model_name = model_name

    def detect_and_encode(self, image_path: str) -> Dict[str, Any]:
        """
        Detects faces in an image and generates feature encodings using DeepFace.
        """
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
            facial_area = embedding_objs[0]["facial_area"]  # {'x', 'y', 'w', 'h'}

            logger.info(f"Successfully detected {len(embedding_objs)} face(s) in {image_path}")

            return {
                "success": True,
                "faces_found": len(embedding_objs),
                "facial_area": facial_area,
                "primary_encoding": primary_embedding,
                "image_path": image_path
            }

        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            return {"success": False, "error": str(e)}

    def extract_face_crop(self, image_path: str, output_path: str) -> Optional[str]:
        """
        Crops and saves the primary detected face to disk.
        """
        result = self.detect_and_encode(image_path)
        if not result["success"]:
            return None

        area = result["facial_area"]
        image = cv2.imread(image_path)
        
        x, y, w, h = area["x"], area["y"], area["w"], area["h"]
        cropped_face = image[y:y+h, x:x+w]
        
        cv2.imwrite(output_path, cropped_face)
        return output_path