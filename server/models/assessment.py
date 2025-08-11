from typing import Any, Dict, Optional

from pydantic import BaseModel


class AssessmentSource(BaseModel):
  """Source of an assessment."""

  source_type: str  # 'HUMAN', 'LLM_JUDGE', etc.
  source_id: str  # username or model id


class Assessment(BaseModel):
  """MLflow trace assessment with value and rationale."""

  assessment_id: Optional[str] = None
  name: str
  value: Any
  type: Optional[str] = None  # 'feedback' or 'expectation'
  rationale: Optional[str] = None
  metadata: Optional[Dict[str, Any]] = None
  source: Optional[AssessmentSource] = None
