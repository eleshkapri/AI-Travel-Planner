# -*- coding: utf-8 -*-
"""
Vercel Serverless Entrypoint for RoamAI.
Directly exports the FastAPI application instance.
"""
import sys
from pathlib import Path

# Ensure project root directory is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import app
