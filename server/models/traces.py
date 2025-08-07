"""Pydantic models for MLflow traces.

This module defines the data models for MLflow trace-related operations,
including search requests/responses and trace data structures.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from server.models.types import Assessment, Span, TraceLocation


class SearchTracesRequest(BaseModel):
  """Request model for searching traces."""

  experiment_ids: Optional[List[str]] = Field(None, description='List of experiment IDs to search')
  filter: Optional[str] = Field(None, description='Search filter string')
  run_id: Optional[str] = Field(None, description='Run ID to filter by')
  max_results: Optional[int] = Field(1000, description='Maximum number of results', ge=1, le=10000)
  page_token: Optional[str] = Field(None, description='Pagination token')
  order_by: Optional[List[str]] = Field(None, description='Sort order')
  include_spans: Optional[bool] = Field(
    False, description='Whether to include span data in results'
  )


class TraceInfo(BaseModel):
  """Trace information model."""

  trace_id: str
  trace_location: TraceLocation
  request_time: str
  execution_duration: str
  state: str
  trace_metadata: Optional[Dict[str, str]] = None
  tags: Optional[Dict[str, str]] = None
  assessments: Optional[List[Assessment]] = None
  request_preview: Optional[str] = Field(None, description='Preview of the request content')
  response_preview: Optional[str] = Field(None, description='Preview of the response content')


class TraceData(BaseModel):
  """Trace data model."""

  spans: List[Span]


class Trace(BaseModel):
  """Full trace model."""

  info: TraceInfo
  data: TraceData


class SearchTracesResponse(BaseModel):
  """Response model for search traces."""

  traces: List[Trace]
  next_page_token: Optional[str] = None


class LinkTracesToRunRequest(BaseModel):
  """Request to link traces to a run."""

  run_id: str
  trace_ids: List[str]
