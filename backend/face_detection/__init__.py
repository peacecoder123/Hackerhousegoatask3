from .detector import FaceDetector

_default_detector = FaceDetector(model_name="Facenet")

def encode_face(image_path: str):
    return _default_detector.detect_and_encode(image_path)

__all__ = ["FaceDetector", "encode_face"]