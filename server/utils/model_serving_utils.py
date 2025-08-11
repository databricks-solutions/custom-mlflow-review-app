"""Model Serving Endpoint Utilities

This module provides utilities for calling Databricks model serving endpoints.
"""

import logging
from typing import Any, Dict, List, Optional

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import DatabricksError
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

# Environment variables loaded by server/__init__.py

logger = logging.getLogger(__name__)


class ModelServingClient:
  """Client for interacting with Databricks model serving endpoints."""

  def __init__(self):
    """Initialize the client with Databricks SDK WorkspaceClient."""
    try:
      self.client = WorkspaceClient()
      logger.info('Initialized Databricks model serving client')
    except Exception as e:
      logger.error(f'Failed to initialize Databricks client: {e}')
      raise

  def query_endpoint(
    self,
    endpoint_name: str,
    messages: List[Dict[str, str]],
    temperature: Optional[float] = 0.7,
    max_tokens: Optional[int] = 1000,
    stream: Optional[bool] = False,
  ) -> Dict[str, Any]:
    """Query a model serving endpoint with chat messages.

    Args:
        endpoint_name: Name of the serving endpoint
        messages: List of message dicts with 'role' and 'content' keys
        temperature: Model temperature (0.0-2.0)
        max_tokens: Maximum tokens to generate
        stream: Whether to enable streaming (default: False)

    Returns:
        Response dictionary with model output

    Raises:
        Exception: If the endpoint call fails
    """
    try:
      logger.info(f'Querying endpoint {endpoint_name} with {len(messages)} messages')
      logger.debug(f'Messages: {messages}')
      logger.debug(
        f'Parameters: temperature={temperature}, max_tokens={max_tokens}, stream={stream}'
      )

      # Convert dict messages to ChatMessage objects
      chat_messages = []
      for msg in messages:
        role_str = msg['role'].upper()
        if role_str == 'USER':
          role = ChatMessageRole.USER
        elif role_str == 'ASSISTANT':
          role = ChatMessageRole.ASSISTANT
        elif role_str == 'SYSTEM':
          role = ChatMessageRole.SYSTEM
        else:
          raise ValueError(f"Invalid message role: {msg['role']}")

        chat_messages.append(ChatMessage(content=msg['content'], role=role))

      response = self.client.serving_endpoints.query(
        name=endpoint_name,
        messages=chat_messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=stream,
      )

      logger.info(f'Successfully received response from {endpoint_name}')
      logger.debug(f'Response type: {type(response)}')

      # Convert response to dict
      return response.as_dict()

    except DatabricksError as e:
      error_msg = f'Databricks API error calling {endpoint_name}: {e}'
      logger.error(error_msg)
      raise Exception(error_msg)
    except Exception as e:
      error_msg = f'Unexpected error calling {endpoint_name}: {e}'
      logger.error(error_msg)
      raise Exception(error_msg)

  def query_claude_sonnet_4(
    self,
    messages: List[Dict[str, str]],
    temperature: Optional[float] = 0.7,
    max_tokens: Optional[int] = 1000,
  ) -> Dict[str, Any]:
    """Convenience method for querying the databricks-claude-sonnet-4 endpoint.

    Args:
        messages: List of message dicts with 'role' and 'content' keys
        temperature: Model temperature (0.0-2.0)
        max_tokens: Maximum tokens to generate

    Returns:
        Response dictionary with model output
    """
    return self.query_endpoint(
      endpoint_name='databricks-claude-sonnet-4',
      messages=messages,
      temperature=temperature,
      max_tokens=max_tokens,
      stream=False,
    )


def create_chat_messages(conversation: List[tuple]) -> List[Dict[str, str]]:
  """Create chat messages from a list of (role, content) tuples.

  Args:
      conversation: List of (role, content) tuples

  Returns:
      List of message dictionaries

  Example:
      messages = create_chat_messages([
          ("user", "Hello"),
          ("assistant", "Hi there!"),
          ("user", "How are you?")
      ])
  """
  return [{'role': role, 'content': content} for role, content in conversation]


def format_response(response: Dict[str, Any]) -> str:
  """Format the model response for display.

  Args:
      response: Raw response from model serving endpoint

  Returns:
      Formatted response text
  """
  try:
    # Try to extract response content from various possible structures
    if hasattr(response, 'predictions') and response.predictions:
      return str(response.predictions[0])
    elif hasattr(response, 'choices') and response.choices:
      return response.choices[0].get('message', {}).get('content', str(response))
    elif isinstance(response, dict):
      # Handle dict response
      if 'predictions' in response and response['predictions']:
        return str(response['predictions'][0])
      elif 'choices' in response and response['choices']:
        return response['choices'][0].get('message', {}).get('content', str(response))

    # Fallback to string representation
    return str(response)

  except Exception as e:
    logger.warning(f'Failed to format response: {e}')
    return str(response)
