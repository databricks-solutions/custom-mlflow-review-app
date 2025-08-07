"""Review Apps endpoints."""

from fastapi import APIRouter, HTTPException

from server.models.review_apps import ReviewApp
from server.utils.config import get_config
from server.utils.review_apps_utils import review_apps_utils

router = APIRouter(prefix='/review-apps', tags=['Review Apps'])


@router.get('/current', response_model=ReviewApp)
async def get_current_review_app() -> ReviewApp:
  """Get THE review app for the configured experiment (cached server-side)."""
  config = get_config()
  experiment_id = config.experiment_id

  if not experiment_id:
    raise HTTPException(status_code=404, detail='No experiment configured')

  result = await review_apps_utils.get_review_app_by_experiment(experiment_id)
  if not result:
    raise HTTPException(
      status_code=404, detail=f'No review app found for experiment {experiment_id}'
    )

  return ReviewApp(**result)


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
