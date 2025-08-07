"""Main router module for the MLflow Review App.

This module organizes API routes into logical groups:
- Core: Configuration and user management
- MLflow: MLflow proxy operations and integrations
- Review: Review apps, labeling sessions, and labeling items
- Traces: Trace analysis and pattern detection
"""

from fastapi import APIRouter

from .core import router as core_router
from .mlflow import router as mlflow_router
from .review import router as review_router
from .traces.analysis import router as traces_router

# Main application router
router = APIRouter()

# Include router groups
router.include_router(core_router)
router.include_router(mlflow_router)
router.include_router(review_router)
router.include_router(traces_router)
