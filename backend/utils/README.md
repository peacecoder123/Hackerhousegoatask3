# `utils/` — Shared Helpers

Utility modules shared across all pipeline steps.

## Files

| File | Purpose |
|------|---------|
| `config.py` | Load and validate environment variables |
| `logger.py` | Consistent structured logging |
| `image_utils.py` | Image download, resizing, format helpers |
| `README.md` | This file |

## Usage

```python
from utils.config import get_config
from utils.logger import get_logger

cfg = get_config()
log = get_logger(__name__)
log.info("Pipeline started", extra={"image": cfg.image_path})
```
