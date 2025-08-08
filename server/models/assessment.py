from typing import Any, Optional, Dict
from pydantic import BaseModel


class AssessmentSource(BaseModel):
    """Source of an assessment."""
    source_type: str  # 'HUMAN', 'LLM_JUDGE', etc.
    source_id: str    # username or model id


class Assessment(BaseModel):
    """MLflow trace assessment with value and rationale."""
    name: str
    value: Any
    rationale: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    source: Optional[AssessmentSource] = None