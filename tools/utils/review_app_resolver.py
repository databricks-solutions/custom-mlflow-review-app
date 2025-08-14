"""Utility for resolving review app ID from experiment or config."""

import sys
from typing import Optional

from server.utils.config import config
from server.utils.review_apps_utils import review_apps_utils


async def resolve_review_app_id(
  review_app_id: Optional[str] = None, experiment_id: Optional[str] = None
) -> tuple[str, dict]:
  """Resolve review app ID from provided arguments or config.

  Args:
      review_app_id: Explicit review app ID
      experiment_id: Experiment ID to find review app

  Returns:
      Tuple of (review_app_id, review_app_data)

  Raises:
      SystemExit: If arguments are invalid or review app not found
  """
  # Validate arguments
  if review_app_id and experiment_id:
    print('❌ Error: Cannot specify both --review-app-id and --experiment-id', file=sys.stderr)
    sys.exit(1)

  # Get review app
  if review_app_id:
    review_app = await review_apps_utils.get_review_app(review_app_id=review_app_id)
  else:
    # Use provided experiment_id or default to config
    exp_id = experiment_id or config.experiment_id
    review_app = await review_apps_utils.get_review_app_by_experiment(experiment_id=exp_id)

  resolved_id = review_app.get('review_app_id')
  if not resolved_id:
    print('❌ Error: Could not resolve review app ID', file=sys.stderr)
    sys.exit(1)

  return resolved_id, review_app


def add_review_app_args(parser, required: bool = False):
  """Add review app related arguments to argument parser.

  Args:
      parser: ArgumentParser instance
      required: Whether review_app_id should be required (for backwards compatibility)
  """
  if required:
    # For backwards compatibility, keep as positional
    parser.add_argument(
      'review_app_id', nargs='?', help='Review app ID (optional, defaults to current experiment)'
    )
  else:
    parser.add_argument('--review-app-id', help='Review app ID (defaults to current experiment)')

  parser.add_argument('--experiment-id', help='Experiment ID (defaults to config experiment_id)')
