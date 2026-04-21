"""
main.py — Analytics Service Entry Point
=========================================
Usage:
    # From services/analytics/
    uvicorn main:app --reload --port 8003

    # Interactive API docs:
    http://localhost:8003/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

app = FastAPI(
    title="Analytics Service",
    description=(
        "Compute KPIs, detect trends, and flag anomalies in your business data. "
        "Powers dashboards and decision support."
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
