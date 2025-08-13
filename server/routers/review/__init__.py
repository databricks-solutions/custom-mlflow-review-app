"""Review App API routers.

This module contains routers for review app domain operations including
review apps, labeling sessions, labeling items, and label schemas management.
"""

from fastapi import APIRouter

from .label_schemas import router as label_schemas_router
from .labeling_items import router as labeling_items_router
from .labeling_sessions import router as labeling_sessions_router
from .review_apps import router as review_apps_router

# Create review app router group
router = APIRouter(tags=['Review Apps'])
router.include_router(review_apps_router)
router.include_router(label_schemas_router)
router.include_router(labeling_sessions_router)
router.include_router(labeling_items_router)

__all__ = ['router']
