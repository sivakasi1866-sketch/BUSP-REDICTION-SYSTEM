# Partners Bus Prediction — Vercel Entry Point
# This file is the serverless function entry for Vercel Python runtime.
# It imports the FastAPI app so Vercel can serve it.

import sys
import os

# Ensure project root is on the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: F401 — Vercel looks for `app`
