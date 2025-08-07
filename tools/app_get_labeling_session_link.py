#!/usr/bin/env python3
"""Generate labeling session links for the local development app."""

import argparse
import json
import os
import subprocess
import sys


def get_app_labeling_session_link(review_app_id: str, labeling_session_id: str) -> str:
  """Generate a local development app labeling session link.

  Args:
      review_app_id: The review app ID
      labeling_session_id: The labeling session ID

  Returns:
      Complete URL to the local labeling session page

  Example:
      http://localhost:5173/review-app/36cb6150924443a9a8abf3209bcffaf8?session=86c89a01-7f31-4cc0-b610-f88c6ab057c2&mode=dev
  """
  return f'http://localhost:5173/review-app/{review_app_id}?session={labeling_session_id}&mode=dev'


def find_labeling_session_by_name(session_name: str, experiment_id: str = None) -> tuple[str, str]:
  """Find a labeling session ID and review app ID by name.

  Args:
      session_name: The name/title of the labeling session to find
      experiment_id: Optional experiment ID to narrow search

  Returns:
      Tuple of (session_id, review_app_id) if found

  Raises:
      ValueError: If session not found or multiple sessions with same name
  """
  try:
    # Call list_labeling_sessions.py to get all sessions
    cmd = [sys.executable, 'tools/list_labeling_sessions.py']
    if experiment_id:
      cmd.extend(['--experiment-id', experiment_id])

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    sessions_data = json.loads(result.stdout)

    # Search for sessions matching the name
    matches = []
    sessions = sessions_data.get('labeling_sessions', [])

    for session in sessions:
      # Check if name matches (case-insensitive)
      if session.get('name', '').lower() == session_name.lower():
        matches.append(session)

    if not matches:
      raise ValueError(f"No labeling session found with name '{session_name}'")

    if len(matches) > 1:
      session_ids = [s.get('labeling_session_id', 'unknown') for s in matches]
      raise ValueError(
        f"Multiple labeling sessions found with name '{session_name}': {session_ids}"
      )

    session_id = matches[0].get('labeling_session_id')
    review_app_id = matches[0].get('review_app_id')

    if not session_id:
      raise ValueError(f"Session '{session_name}' found but has no ID")
    if not review_app_id:
      raise ValueError(f"Session '{session_name}' found but has no review app ID")

    return session_id, review_app_id

  except subprocess.CalledProcessError as e:
    raise ValueError(f'Failed to list labeling sessions: {e.stderr}')
  except json.JSONDecodeError:
    raise ValueError('Failed to parse labeling sessions response')


def main():
  """Generate local app labeling session link."""
  parser = argparse.ArgumentParser(
    description='Generate local app labeling session link',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
    python app_get_labeling_session_link.py 36cb6150924443a9a8abf3209bcffaf8 86c89a01-7f31-4cc0-b610-f88c6ab057c2
    python app_get_labeling_session_link.py 36cb6150924443a9a8abf3209bcffaf8 "test-session-name" --by-name
        """,
  )

  parser.add_argument('review_app_id', help='Review app ID')

  parser.add_argument(
    'labeling_session_id',
    help='Labeling session ID or name (will search by name if not a valid UUID)',
  )

  parser.add_argument(
    '--by-name', action='store_true', help='Force search by name instead of treating as ID'
  )

  parser.add_argument(
    '--help-detailed', action='store_true', help='Show detailed help with examples'
  )

  if '--help-detailed' in os.sys.argv:
    print("""
Local App Labeling Session Link Generator

This tool generates direct links to labeling sessions in the local development
application interface.

URL Structure:
    http://localhost:5173/review-app/{review_app_id}?session={labeling_session_id}&mode=dev

Parameters:
    review_app_id: The review app ID
    labeling_session_id: The specific labeling session ID or name

Usage Examples:
    # Generate link for a specific labeling session
    python app_get_labeling_session_link.py 36cb6150924443a9a8abf3209bcffaf8 86c89a01-7f31-4cc0-b610-f88c6ab057c2

    # Search by session name
    python app_get_labeling_session_link.py 36cb6150924443a9a8abf3209bcffaf8 "test-session-1" --by-name

    # Open link directly in browser (macOS)
    open $(python app_get_labeling_session_link.py 36cb6150924443a9a8abf3209bcffaf8 86c89a01-7f31-4cc0-b610-f88c6ab057c2)

Integration Notes:
    - Use this tool to generate links for local development and testing
    - Links provide direct access to the labeling interface in dev mode
    - Requires the development server to be running on localhost:5173
    - Links work for local development and debugging purposes
        """)
    return

  args = parser.parse_args()

  try:
    session_id = args.labeling_session_id
    review_app_id = args.review_app_id

    # Determine if we should search by name
    should_search_by_name = args.by_name or (
      # If it's not a UUID-like string, assume it's a name
      not (len(session_id) == 36 and session_id.count('-') == 4)
    )

    if should_search_by_name:
      # Search for session by name
      print(f"Searching for labeling session named '{session_id}'...", file=sys.stderr)
      session_id, found_review_app_id = find_labeling_session_by_name(session_id)
      print(
        f'Found session ID: {session_id}, review app ID: {found_review_app_id}', file=sys.stderr
      )
      # Use the found review app ID if we found one
      review_app_id = found_review_app_id

    link = get_app_labeling_session_link(review_app_id, session_id)
    print(link)
  except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    return 1

  return 0


if __name__ == '__main__':
  exit(main())
