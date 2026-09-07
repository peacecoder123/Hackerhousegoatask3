"""
conftest.py
-----------
Pytest configuration for the backend/ directory.

Adds `backend/` itself to sys.path so that tests can import modules
as `from blockchain.fingerprint import ...` without needing to install
the package.
"""
import sys
from pathlib import Path

# Insert the backend/ directory into sys.path
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
