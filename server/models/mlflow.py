"""Pydantic models for MLflow API requests and responses.

This module defines type-safe models for MLflow API operations,
replacing generic Dict[str, Any] with proper typed structures.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from server.models.types import MLflowExperimentInfo, MLflowRunInfo


class CreateRunRequest(BaseModel):
  """Request to create an MLflow run."""

  experiment_id: str
  user_id: Optional[str] = None
  start_time: Optional[int] = None
  tags: Optional[Dict[str, str]] = None


class CreateRunResponse(BaseModel):
  """Response from creating an MLflow run."""

  run: MLflowRunInfo


class UpdateRunRequest(BaseModel):
  """Request to update an MLflow run."""

  run_id: str
  status: Optional[str] = None
  end_time: Optional[int] = None
  tags: Optional[List[Dict[str, str]]] = None


class SearchRunsRequest(BaseModel):
  """Request to search for MLflow runs."""

  experiment_ids: List[str]
  filter: Optional[str] = None
  run_view_type: Optional[str] = 'ACTIVE_ONLY'
  max_results: Optional[int] = 1000
  order_by: Optional[List[str]] = None
  page_token: Optional[str] = None


class SearchRunsResponse(BaseModel):
  """Response from searching runs."""

  runs: List[MLflowRunInfo]
  next_page_token: Optional[str] = None


class GetExperimentResponse(BaseModel):
  """Response from getting an experiment."""

  experiment: MLflowExperimentInfo


class GetRunResponse(BaseModel):
  """Response from getting a run."""

  run: MLflowRunInfo


class LinkTracesResponse(BaseModel):
  """Response from linking traces to a run."""

  success: bool
  linked_count: int
  message: Optional[str] = None


class LogFeedbackRequest(BaseModel):
  """Request to log feedback on a trace."""

  feedback_key: str
  feedback_value: Union[str, int, float, bool, List[Union[str, int, float, bool]]]
  rationale: Optional[str] = None


class LogExpectationRequest(BaseModel):
  """Request to log expectation on a trace."""

  expectation_key: str
  expectation_value: Union[
    str, int, float, bool, List[Union[str, int, float, bool]], Dict[str, Any]
  ]
  rationale: Optional[str] = None


class LogFeedbackResponse(BaseModel):
  """Response from logging feedback."""

  success: bool
  message: Optional[str] = None
  assessment_id: Optional[str] = None


class LogExpectationResponse(BaseModel):
  """Response from logging expectation."""

  success: bool
  message: Optional[str] = None
  assessment_id: Optional[str] = None


class UpdateFeedbackRequest(BaseModel):
  """Request to update existing feedback on a trace."""

  assessment_id: str
  feedback_value: Union[str, int, float, bool, List[Union[str, int, float, bool]]]
  rationale: Optional[str] = None


class UpdateExpectationRequest(BaseModel):
  """Request to update existing expectation on a trace."""

  assessment_id: str
  expectation_value: Union[
    str, int, float, bool, List[Union[str, int, float, bool]], Dict[str, Any]
  ]
  rationale: Optional[str] = None


class UpdateFeedbackResponse(BaseModel):
  """Response from updating feedback."""

  success: bool
  message: Optional[str] = None
  assessment_id: Optional[str] = None


class UpdateExpectationResponse(BaseModel):
  """Response from updating expectation."""

  success: bool
  message: Optional[str] = None
  assessment_id: Optional[str] = None
