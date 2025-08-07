"""Pydantic models for Review Apps.

This module defines the data models for Review Apps, Labeling Sessions,
and Labeling Items used in the MLflow Review App.
"""

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field

from server.models.types import (
  AgentConfig,
  ChatRound,
  DatasetConfig,
  DatasetSource,
  LabelingSchemaRef,
  LabelValue,
  TraceSource,
)


class ModelServingEndpoint(BaseModel):
  """Model serving endpoint configuration."""

  endpoint_name: str
  served_entity_name: str


class Agent(BaseModel):
  """Agent configuration for review app."""

  agent_name: str
  model_serving_endpoint: Optional[ModelServingEndpoint] = None


class LabelingSchema(BaseModel):
  """Labeling schema configuration."""

  name: str
  type: Literal['FEEDBACK', 'EXPECTATION']
  title: str
  instruction: Optional[str] = None
  enable_comment: Optional[bool] = False
  # Schema types (only one should be set)
  categorical: Optional[Dict[str, List[str]]] = None  # {"options": ["opt1", "opt2"]}
  categorical_list: Optional[Dict[str, List[str]]] = None
  text: Optional[Dict[str, int]] = None  # {"max_length": 500}
  text_list: Optional[Dict[str, Any]] = None  # {"max_length_each": 100, "max_count": 5}
  numeric: Optional[Dict[str, float]] = None  # {"min_value": 0, "max_value": 10}


class ReviewApp(BaseModel):
  """Review app model."""

  review_app_id: Optional[str] = None
  experiment_id: str
  agents: Optional[List[Agent]] = Field(default_factory=list)
  labeling_schemas: Optional[List[LabelingSchema]] = Field(default_factory=list)


class ListReviewAppsResponse(BaseModel):
  """Response for listing review apps."""

  review_apps: List[ReviewApp]
  next_page_token: Optional[str] = None


class LabelingSession(BaseModel):
  """Labeling session model."""

  labeling_session_id: Optional[str] = None
  mlflow_run_id: Optional[str] = None
  create_time: Optional[str] = None
  created_by: Optional[str] = None
  last_update_time: Optional[str] = None
  last_updated_by: Optional[str] = None
  name: str
  assigned_users: Optional[List[str]] = Field(default_factory=list)
  agent: Optional[AgentConfig] = None
  labeling_schemas: Optional[List[LabelingSchemaRef]] = Field(default_factory=list)
  dataset: Optional[DatasetConfig] = None
  additional_configs: Optional[Dict[str, Any]] = None


class ListLabelingSessionsResponse(BaseModel):
  """Response for listing labeling sessions."""

  labeling_sessions: List[LabelingSession]
  next_page_token: Optional[str] = None


class ItemState(str, Enum):
  """Item state enum."""

  PENDING = 'PENDING'
  IN_PROGRESS = 'IN_PROGRESS'
  COMPLETED = 'COMPLETED'
  SKIPPED = 'SKIPPED'


class Item(BaseModel):
  """Labeling session item."""

  item_id: Optional[str] = None
  create_time: Optional[str] = None
  created_by: Optional[str] = None
  last_update_time: Optional[str] = None
  last_updated_by: Optional[str] = None
  source: Optional[Union[TraceSource, DatasetSource]] = None
  state: Optional[ItemState] = ItemState.PENDING
  chat_rounds: Optional[List[ChatRound]] = Field(default_factory=list)
  labels: Optional[Dict[str, LabelValue]] = None
  # Preview fields for UI display
  request_preview: Optional[str] = Field(None, description='Preview of the request content')
  response_preview: Optional[str] = Field(None, description='Preview of the response content')


class ListItemsResponse(BaseModel):
  """Response for listing items."""

  items: List[Item]
  next_page_token: Optional[str] = None


class BatchCreateItemsRequest(BaseModel):
  """Request to batch create items."""

  items: List[Dict[str, Any]]


class LinkTracesToSessionRequest(BaseModel):
  """Request to link traces to a labeling session."""

  mlflow_run_id: str
  trace_ids: List[str]


class LinkTracesToSessionResponse(BaseModel):
  """Response from linking traces to a labeling session."""

  success: bool
  linked_traces: int
  message: Optional[str] = None
  items_created: Optional[int] = None
