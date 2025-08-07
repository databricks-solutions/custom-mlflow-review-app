#!/usr/bin/env python3
"""Test script to query databricks-claude-sonnet-4 model serving endpoint."""

import json

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import DatabricksError


def test_claude_sonnet_4():
  """Test the databricks-claude-sonnet-4 serving endpoint."""
  # Initialize client
  client = WorkspaceClient()
  endpoint_name = 'databricks-claude-sonnet-4'

  print(f'Testing {endpoint_name} endpoint...')
  print('=' * 50)

  try:
    # First, check if the endpoint exists and get its details
    endpoint = client.serving_endpoints.get(endpoint_name)

    print(f'✓ Endpoint found: {endpoint.name}')
    print(f'  State: {endpoint.state}')

    # Check if endpoint is ready
    if (
      hasattr(endpoint.state, 'ready')
      and hasattr(endpoint.state.ready, 'value')
      and endpoint.state.ready.value != 'READY'
    ):
      print(f'❌ Endpoint not ready. Current state: {endpoint.state}')
      return

    print('✓ Endpoint is ready')

    # Prepare the chat input for Claude
    chat_input = {
      'messages': [{'role': 'user', 'content': 'How tall is the eiffel tower?'}],
      'max_tokens': 150,
      'temperature': 0.7,
    }

    print(f'\n📤 Sending query: {chat_input["messages"][0]["content"]}')

    # Query the endpoint using the SDK's query method
    print('📡 Querying endpoint...')

    # Check authentication first
    print('🔍 Authentication check:')
    print(f'  Client config host: {client.config.host}')
    print(f'  Token available: {bool(client.config.token)}')

    if not client.config.token:
      print('⚠️ No token directly available, but endpoint listing worked, so trying query anyway...')
    else:
      print('✅ Token available')

    # Try to query the endpoint using the SDK with proper ChatMessage format
    try:
      # Import ChatMessage and ChatMessageRole classes
      from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

      # Create proper ChatMessage objects
      messages = [ChatMessage(role=ChatMessageRole.USER, content='How tall is the eiffel tower?')]

      # Use the SDK's query method with proper parameters
      response = client.serving_endpoints.query(
        name=endpoint_name, messages=messages, max_tokens=150, temperature=0.7
      )

      print('✅ Response received via SDK:')
      print(f'Response type: {type(response)}')
      print(f'Response: {response}')

      # Try to extract the actual answer
      if hasattr(response, 'choices') and response.choices:
        answer = response.choices[0].message.content
        print(f'Answer: {answer}')
      elif hasattr(response, 'data'):
        print(f'Response data: {response.data}')
      else:
        print(f'Full response: {response}')

      return

    except Exception as sdk_error:
      print(f'⚠️ SDK query with ChatMessage failed: {sdk_error}')

      # Show the method signature for debugging
      print('\n🔍 SDK query method signature:')
      import inspect

      sig = inspect.signature(client.serving_endpoints.query)
      print(f'  {sig}')

      return

    if response.status_code == 200:
      result = response.json()
      print('\n✅ Response received:')
      print(f'Status: {response.status_code}')

      # Handle different response formats
      if 'choices' in result:
        # OpenAI-style response
        answer = result['choices'][0]['message']['content']
        print(f'Answer: {answer}')
      elif 'content' in result:
        # Direct content response
        print(f'Answer: {result["content"]}')
      elif 'response' in result:
        # Response field
        print(f'Answer: {result["response"]}')
      else:
        # Print full response if format is unknown
        print(f'Full response: {json.dumps(result, indent=2)}')

    else:
      print(f'❌ Error: HTTP {response.status_code}')
      print(f'Response: {response.text}')

  except DatabricksError as e:
    if 'NOT_FOUND' in str(e):
      print(f"❌ Endpoint '{endpoint_name}' not found")
      print('\nAvailable endpoints:')
      try:
        endpoints = client.serving_endpoints.list()
        for ep in endpoints:
          print(f'  - {ep.name} ({ep.state})')
      except Exception as list_error:
        print(f'  Could not list endpoints: {list_error}')
    else:
      print(f'❌ Databricks error: {e}')

  except Exception as timeout_error:
    if 'timeout' in str(timeout_error).lower():
      print('❌ Request timeout - endpoint may be slow')
    elif 'connection' in str(timeout_error).lower():
      print('❌ Connection error - check network')
    else:
      print(f'❌ Request error: {timeout_error}')

  except Exception as e:
    print(f'❌ Unexpected error: {e}')
    import traceback

    traceback.print_exc()


if __name__ == '__main__':
  test_claude_sonnet_4()
