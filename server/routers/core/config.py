"""Configuration endpoints for the MLflow Review App."""

from typing import Any, Dict, Optional

from fastapi import APIRouter

from server.utils.config import config

router = APIRouter(prefix='/config', tags=['Configuration'])


@router.get('/')
async def get_config() -> Dict[str, Any]:
  """Get application configuration.

  Returns:
      Dictionary containing public configuration values
  """
  return {
    'experiment_id': config.experiment_id,
    'max_results': config.max_results,
    'page_size': config.page_size,
    'debug': config.debug,
  }


@router.get('/experiment-id')
async def get_experiment_id() -> Dict[str, Optional[str]]:
  """Get the primary experiment ID.

  Returns:
      Dictionary containing the experiment ID
  """
  return {'experiment_id': config.experiment_id}
