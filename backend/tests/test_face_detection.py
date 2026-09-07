import os
import sys

# Ensure backend root is in Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from face_detection.detector import FaceDetector

def test_detection():
    detector = FaceDetector(model_name="Facenet")
    
    # Path to sample image inside backend/tests/
    sample_image = os.path.join(os.path.dirname(__file__), "sample_face.jpg")
    
    print(f"Testing image path: {sample_image}")
    result = detector.detect_and_encode(sample_image)
    
    print("\n--- Detection Result ---")
    print(f"Success: {result.get('success')}")
    print(f"Faces Found: {result.get('faces_found')}")
    
    if result.get("success"):
        encoding = result.get("primary_encoding")
        print(f"Embedding Vector Dimension: {len(encoding)}")
        print("Face Detection & Encoding Test PASSED!")
    else:
        print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    test_detection()