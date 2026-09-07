"""
face_detection/detector.py
---------------------------
Face detection and embedding using facenet-pytorch.

Uses MTCNN for face detection and InceptionResnetV1 (Facenet) for embedding.
This is a drop-in replacement for the deepface backend — the public return
dict is identical so pipeline.py and all other callers are unaffected.

Why facenet-pytorch instead of deepface?
  deepface >= 0.0.79 unconditionally imports tensorflow at module level.
  TensorFlow has no Python 3.14 wheel. facenet-pytorch provides the same
  Facenet model using PyTorch, which supports Python 3.14.

Member 1 owns this file.
"""
import os
import torch
import numpy as np
import cv2
from typing import Dict, Any

from facenet_pytorch import MTCNN, InceptionResnetV1

try:
    from utils.logger import get_logger
    logger = get_logger("face_detector")
except Exception:
    import logging
    logger = logging.getLogger("face_detector")


class FaceDetector:
    def __init__(self, model_name: str = "Facenet"):
        # model_name kept for API compatibility; we always use InceptionResnetV1
        self.model_name = model_name
        self._device = torch.device("cpu")
        # MTCNN: face detector — returns aligned 160×160 crops
        self._mtcnn = MTCNN(
            image_size=160,
            margin=20,
            min_face_size=20,
            thresholds=[0.6, 0.7, 0.7],
            keep_all=False,        # return only the primary (highest-conf) face
            device=self._device,
            post_process=True,
        )
        # InceptionResnetV1: Facenet model pretrained on VGGFace2
        self._resnet = InceptionResnetV1(pretrained="vggface2").eval().to(self._device)

    def detect_and_encode(self, image_path: str) -> Dict[str, Any]:
        if not os.path.exists(image_path):
            logger.error(f"Image path does not exist: {image_path}")
            return {"success": False, "error": f"File not found: {image_path}"}

        try:
            # ── Load image ───────────────────────────────────────────────────
            bgr = cv2.imread(image_path)
            if bgr is None:
                return {
                    "success": False,
                    "error": f"cv2 could not read image: {image_path}",
                }
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

            # ── Detect face + get bounding box ────────────────────────────────
            from PIL import Image as PILImage
            pil_img = PILImage.fromarray(rgb)

            # detect() → (boxes, probs): get bounding box + confidence
            boxes, probs = self._mtcnn.detect(pil_img)
            if boxes is None or probs is None or len(boxes) == 0:
                logger.warning(f"No face detected in {image_path}")
                return {
                    "success": False,
                    "error": "No face detected in the provided image scan.",
                    "faces_found": 0,
                }

            # __call__() → aligned 160×160 crop for embedding
            face_tensor = self._mtcnn(pil_img)

            if face_tensor is None:
                logger.warning(f"No face detected in {image_path}")
                return {
                    "success": False,
                    "error": "No face detected in the provided image scan.",
                    "faces_found": 0,
                }

            confidence = float(probs[0])
            x1, y1, x2, y2 = [int(v) for v in boxes[0]]
            w, h = x2 - x1, y2 - y1
            facial_area = {"x": x1, "y": y1, "w": w, "h": h}
            bbox = [x1, y1, w, h]

            # ── Generate 512-dim Facenet embedding ───────────────────────────
            face_batch = face_tensor.unsqueeze(0).to(self._device)  # [1, 3, 160, 160]
            with torch.no_grad():
                embedding_tensor = self._resnet(face_batch)          # [1, 512]

            embedding: list = embedding_tensor[0].cpu().numpy().tolist()

            logger.info(f"Successfully detected face in {image_path} (conf={confidence:.3f})")

            return {
                "success": True,
                "faces_found": 1,
                "facial_area": facial_area,
                "bbox": bbox,
                "primary_encoding": embedding,   # 512-dim float list
                "confidence": confidence,
                "image_path": image_path,
            }

        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            return {"success": False, "error": str(e)}