"""Core API routers.

This module contains routers for fundamental application functionality
including configuration management and user operations.
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .config import router as config_router
from .experiment_summary import router as experiment_summary_router
from .user import router as user_router

# Create core router that includes all core functionality
router = APIRouter(tags=['Core'])
router.include_router(auth_router)
router.include_router(config_router)
router.include_router(user_router, prefix='/user', tags=['User'])
router.include_router(experiment_summary_router)

__all__ = ['router']
