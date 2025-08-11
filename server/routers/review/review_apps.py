"""Review Apps endpoints."""

from fastapi import APIRouter, HTTPException

from server.models.review_apps import ReviewApp
from server.utils.review_apps_utils import review_apps_utils

router = APIRouter(prefix='/review-apps', tags=['Review Apps'])


@router.get('/{review_app_id}', response_model=ReviewApp)
async def get_review_app(review_app_id: str) -> ReviewApp:
  """Get a specific review app by ID."""
  try:
    result = await review_apps_utils.get_review_app(review_app_id)
    if not result:
      raise HTTPException(status_code=404, detail=f'Review app {review_app_id} not found')

    return ReviewApp(**result)
  except Exception as e:
    raise HTTPException(status_code=404, detail=f'Review app {review_app_id} not found: {str(e)}')
