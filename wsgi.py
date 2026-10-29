"""
Grain Guardian - Production WSGI Entry Point
Supports running from repository root via:
  gunicorn wsgi:app
"""

import sys
import os

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import app

if __name__ == "__main__":
    app.run()
