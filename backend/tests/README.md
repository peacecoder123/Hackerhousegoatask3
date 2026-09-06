# `tests/` — Unit & Integration Tests

## Structure

```
tests/
├── test_face_detection.py   # Unit tests for encode_face()
├── test_web_search.py       # Unit tests for search_by_image()
├── test_blockchain.py       # Unit tests for fingerprint, upload, verify
├── test_pipeline.py         # Integration test — full end-to-end mock run
└── README.md                # This file
```

## Running Tests

```bash
cd backend/
pip install pytest pytest-mock
pytest tests/ -v
```

## Conventions

- Use `pytest-mock` for mocking external APIs (SerpAPI, Web3 RPC)
- Use `tmp_path` fixture for temporary image files
- Each module should have ≥80% test coverage
