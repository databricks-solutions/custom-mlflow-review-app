"""Trace pattern analysis endpoints.

This module provides FastAPI endpoints for analyzing trace patterns and agent workflows.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from server.exceptions import MLflowError
from server.utils.trace_analysis import analyze_trace_patterns

router = APIRouter(prefix='/traces', tags=['Trace Analysis'])


class TraceAnalysisResponse(BaseModel):
  """Response model for trace pattern analysis."""

  analysis_summary: dict
  span_patterns: dict
  tool_usage: dict
  input_output_patterns: dict
  conversation_flow: dict


@router.get('/analyze-patterns', response_model=TraceAnalysisResponse)
async def analyze_trace_patterns_endpoint(
  limit: int = Query(default=10, ge=1, le=100, description='Number of recent traces to analyze'),
  experiment_id: Optional[str] = Query(
    default=None, description='Experiment ID to analyze (defaults to config experiment_id)'
  ),
) -> TraceAnalysisResponse:
  """Analyze patterns in recent traces to understand agent architecture and workflows.

  This endpoint examines the structure of traces to identify:
  - Span types and hierarchy patterns
  - Tool usage and calling patterns
  - Conversation flow and message formats
  - Input/output data structures
  - Agent workflow patterns (RAG, function calling, etc.)
  """
  try:
    result = analyze_trace_patterns(experiment_id=experiment_id, limit=limit)

    return TraceAnalysisResponse(**result)

  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
  except Exception as e:
    raise MLflowError(f'Failed to analyze trace patterns: {str(e)}')
