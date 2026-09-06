# `face_detection/` — Face Detection & Embedding

**Owner: Member 1 (Face Identification Engineer)**

## Responsibility

This module is the first step in the pipeline:

1. Load the input image
2. Detect face(s) using a face recognition library
3. Encode the detected face into a 128-dimensional embedding vector
4. Return the embedding + detection metadata (confidence, bounding box)

## Files

| File | Purpose |
|------|---------|
| `detector.py` | Core face detection and encoding logic |
| `models/` | Pre-trained model weights (downloaded on first run) |
| `README.md` | This file |

## Recommended Libraries

- [`face_recognition`](https://github.com/ageitgey/face_recognition) (wraps dlib) — simplest API
- [`deepface`](https://github.com/serengil/deepface) — supports multiple backends (VGG-Face, ArcFace, Facenet)
- AWS Rekognition — cloud-based, no local model needed

## Usage

```python
from face_detection.detector import encode_face

result = encode_face("path/to/face.jpg")
# result = { "embedding": [...128 floats...], "confidence": 0.928, "bbox": [x, y, w, h] }
```

## Output Contract

```json
{
  "embedding": [0.12, -0.45, ...],   // 128-d float vector
  "confidence": 0.928,               // 0–1, detection confidence
  "bbox": [120, 45, 200, 280]        // [x, y, width, height] in pixels
}
```

## Known Limitations

- Requires a clear, front-facing photo for best accuracy
- Low-resolution or heavily occluded faces may fail detection
- Multiple faces in one image: only the largest/most confident face is used
