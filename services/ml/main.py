"""
main.py — ML Service Entry Point
==================================
Starts the FastAPI application for the predictive ML service.

Usage:
    # From services/ml/
    uvicorn main:app --reload --port 8002

    # Interactive API docs:
    http://localhost:8002/docs
"""

import os
import sys

# Make the shared/ package importable when running from services/ml/
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

app = FastAPI(
    title="Predictive ML Service",
    description=(
        "Train regression models on your business data and get predictions "
        "with SHAP-powered plain-English explanations."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
