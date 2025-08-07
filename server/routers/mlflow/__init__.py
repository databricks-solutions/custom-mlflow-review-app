"""MLflow API routers.

This module contains routers for MLflow operations including experiments,
runs, traces, and other MLflow SDK functionality.
"""

from fastapi import APIRouter

from .mlflow import router as mlflow_router

# Create MLflow router group
router = APIRouter(tags=['MLflow'])
router.include_router(mlflow_router)

__all__ = ['router']
