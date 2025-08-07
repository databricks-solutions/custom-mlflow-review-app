"""Review App API routers.

This module contains routers for review app domain operations including
review apps, labeling sessions, and labeling items management.
"""

from fastapi import APIRouter

from .labeling_items import router as labeling_items_router
from .labeling_sessions import router as labeling_sessions_router
from .review_apps import router as review_apps_router

# Create review app router group
router = APIRouter(tags=['Review Apps'])
router.include_router(review_apps_router)
router.include_router(labeling_sessions_router)
router.include_router(labeling_items_router)

__all__ = ['router']
