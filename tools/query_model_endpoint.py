#!/usr/bin/env python3
"""Query Model Serving Endpoint Tool

Test tool for querying Databricks model serving endpoints.
"""

import argparse
import json
import os
import sys

# Add the server directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from utils.config import config
from utils.model_serving_utils import ModelServingClient, format_response


def main():
  parser = argparse.ArgumentParser(
    description='Query Databricks model serving endpoints',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # Query databricks-claude-sonnet-4 with simple message
  python tools/query_model_endpoint.py --endpoint databricks-claude-sonnet-4 --message "Hello, how are you?"
  
  # Query with conversation history
  python tools/query_model_endpoint.py --endpoint databricks-claude-sonnet-4 \\
    --conversation "user:test" "assistant:Hello! I'm working fine. How can I help you today?" "user:test"
  
  # Query with custom parameters
  python tools/query_model_endpoint.py --endpoint databricks-claude-sonnet-4 \\
    --message "Write a short poem" --temperature 0.9 --max-tokens 200
  
  # Query custom endpoint
  python tools/query_model_endpoint.py --endpoint my-custom-endpoint --message "Hello"
        """,
  )

  parser.add_argument(
    '--endpoint',
    default=None,
    help='Name of the serving endpoint (default: from MODEL_ENDPOINT env var)',
  )

  parser.add_argument('--message', help='Single message to send (creates a user message)')

  parser.add_argument(
    '--conversation', nargs='*', help='Conversation history as "role:content" pairs'
  )

  parser.add_argument(
    '--temperature', type=float, default=0.7, help='Model temperature (0.0-2.0, default: 0.7)'
  )

  parser.add_argument(
    '--max-tokens', type=int, default=1000, help='Maximum tokens to generate (default: 1000)'
  )

  parser.add_argument('--json', action='store_true', help='Output raw JSON response')

  parser.add_argument('--debug', action='store_true', help='Enable debug logging')

  args = parser.parse_args()

  # Use config fallback for endpoint
  args.endpoint = args.endpoint or config.model_endpoint

  # Set up logging
  import logging

  level = logging.DEBUG if args.debug else logging.INFO
  logging.basicConfig(level=level, format='%(levelname)s: %(message)s')

  try:
    # Build messages
    messages = []

    if args.conversation:
      # Parse conversation format "role:content"
      for item in args.conversation:
        if ':' not in item:
          print(f"Error: Conversation item '{item}' must be in format 'role:content'")
          sys.exit(1)
        role, content = item.split(':', 1)
        messages.append({'role': role.strip(), 'content': content.strip()})
    elif args.message:
      # Single user message
      messages = [{'role': 'user', 'content': args.message}]
    else:
      # Default test conversation
      messages = [
        {'role': 'user', 'content': 'test'},
        {'role': 'assistant', 'content': "Hello! I'm working fine. How can I help you today?"},
        {'role': 'user', 'content': 'test'},
      ]

    print(f'🤖 Querying endpoint: {args.endpoint}')
    print(f'📝 Messages: {len(messages)} messages')
    print(f'🌡️  Temperature: {args.temperature}')
    print(f'🎯 Max tokens: {args.max_tokens}')
    print('-' * 50)

    # Show conversation
    for i, msg in enumerate(messages, 1):
      print(f"{i}. [{msg['role'].upper()}]: {msg['content']}")
    print('-' * 50)

    # Initialize client and query
    client = ModelServingClient()

    response = client.query_endpoint(
      endpoint_name=args.endpoint,
      messages=messages,
      temperature=args.temperature,
      max_tokens=args.max_tokens,
    )

    # Output response
    if args.json:
      print(json.dumps(response, indent=2, default=str))
    else:
      print('✅ Response:')
      print(format_response(response))
      print('-' * 50)
      print('✅ Query completed successfully!')

  except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)


if __name__ == '__main__':
  main()
