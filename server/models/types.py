"""Common type definitions for the MLflow Review App.

This module contains shared type definitions that are used across
multiple models and modules to improve type safety and reduce
the use of Dict[str, Any].
"""

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel
from typing_extensions import TypedDict


class TraceLocation(TypedDict):
  """Location information for a trace."""

  experiment_id: str
  run_id: str


class SpanType(str):
  """Valid span types in MLflow traces."""

  LLM = 'LLM'
  CHAT_MODEL = 'CHAT_MODEL'
  RETRIEVER = 'RETRIEVER'
  CHAIN = 'CHAIN'
  AGENT = 'AGENT'
  TOOL = 'TOOL'
  UNKNOWN = 'UNKNOWN'


class SpanStatus(TypedDict):
  """Status information for a span."""

  status_code: Literal['OK', 'ERROR']
  description: Optional[str]


class LLMInputs(TypedDict, total=False):
  """Input parameters for LLM spans."""

  messages: List[Dict[str, str]]
  prompt: Optional[str]
  temperature: Optional[float]
  max_tokens: Optional[int]
  model: Optional[str]


class LLMOutputs(TypedDict, total=False):
  """Output data from LLM spans."""

  choices: List[Dict[str, Any]]
  usage: Dict[str, int]
  model: Optional[str]


class SpanInputsOutputs(TypedDict, total=False):
  """Generic inputs/outputs for spans."""

  inputs: Union[LLMInputs, Dict[str, Any]]
  outputs: Union[LLMOutputs, Dict[str, Any]]


class Span(BaseModel):
  """A single span within a trace."""

  name: str
  span_id: str
  parent_id: Optional[str] = None
  start_time_ms: int
  end_time_ms: int
  status: SpanStatus
  span_type: str
  inputs: Optional[Any] = None  # Can be dict, list, str, etc.
  outputs: Optional[Any] = None  # Can be dict, list, str, etc.
  attributes: Optional[Dict[str, Any]] = None


class Assessment(BaseModel):
  """Assessment/evaluation of a trace."""

  assessment_id: Optional[str] = None
  name: str
  value: Union[float, int, str, bool, List[str], Dict[str, Any]]
  type: Optional[str] = None  # 'feedback' or 'expectation'
  rationale: Optional[str] = None
  metadata: Optional[Dict[str, Any]] = None
  source: Optional[Union[str, Dict[str, Any]]] = None


class TraceSource(BaseModel):
  """Source reference for a trace in a labeling session."""

  trace_id: str
  experiment_id: Optional[str] = None
  run_id: Optional[str] = None


class DatasetSource(BaseModel):
  """Dataset source for a labeling item."""

  dataset_name: Optional[str] = None
  dataset_digest: Optional[str] = None
  dataset_index: Optional[int] = None


class ChatMessage(TypedDict):
  """A single message in a chat conversation."""

  role: Literal['system', 'user', 'assistant']
  content: str


class ChatRound(TypedDict, total=False):
  """A round of chat interaction in labeling."""

  # For trace references (when items are created from traces)
  trace_id: Optional[str]

  # For actual chat rounds (when labeling is in progress)
  request: Optional[Dict[str, Any]]
  response: Optional[Dict[str, Any]]
  labels: Optional[Dict[str, Any]]


class LabelValue(BaseModel):
  """A label value with optional comment."""

  value: Union[str, int, float, List[str]]
  comment: Optional[str] = None


class AgentConfig(TypedDict):
  """Agent configuration reference."""

  agent_name: str


class LabelingSchemaRef(TypedDict):
  """Reference to a labeling schema."""

  name: str


class DatasetConfig(TypedDict, total=False):
  """Dataset configuration for labeling session."""

  dataset_name: str
  dataset_digest: str
  filters: Optional[List[Dict[str, Any]]]


# API Response Types
class DatabricksAPIResponse(TypedDict):
  """Generic Databricks API response structure."""

  error_code: Optional[str]
  message: Optional[str]


class MLflowRunInfo(TypedDict):
  """MLflow run information."""

  run_id: str
  run_uuid: str
  experiment_id: str
  user_id: str
  status: str
  start_time: int
  end_time: Optional[int]
  artifact_uri: str
  lifecycle_stage: str


class MLflowExperimentInfo(TypedDict):
  """MLflow experiment information."""

  experiment_id: str
  name: str
  artifact_location: str
  lifecycle_stage: str
  creation_time: int
  last_update_time: int
