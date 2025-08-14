#!/usr/bin/env python3
"""Delete a labeling session from a review app."""

import argparse
import asyncio
import sys

from server.utils.labeling_sessions_utils import (
  delete_labeling_session,
  get_labeling_session,
  get_session_by_name,
  list_labeling_sessions,
)
from tools.utils.review_app_resolver import resolve_review_app_id


async def main():
  """Delete a labeling session from a review app."""
  parser = argparse.ArgumentParser(
    description='Delete a labeling session from a review app',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # Delete a specific session by ID (uses current experiment)
  python delete_labeling_session.py session_id

  # Delete with specific review app ID
  python delete_labeling_session.py review_app_id --name "Test Session"

  # Delete with specific experiment ID
  python delete_labeling_session.py --experiment-id exp123 session_id --dry-run

  # Skip confirmation prompt
  python delete_labeling_session.py session_id --force
        """,
  )

  # For backwards compatibility, keep positional argument but make it optional
  parser.add_argument(
    'review_app_id', nargs='?', help='Review app ID (optional, defaults to current experiment)'
  )
  parser.add_argument('--experiment-id', help='Experiment ID (defaults to config experiment_id)')
  parser.add_argument('session_id', nargs='?', help='Labeling session ID to delete')
  parser.add_argument('--name', help='Delete session by name (alternative to session_id)')
  parser.add_argument(
    '--dry-run', action='store_true', help='Show what would be deleted without actually deleting'
  )
  parser.add_argument('--force', action='store_true', help='Skip confirmation prompts')

  args = parser.parse_args()

  # Validate arguments
  if not args.session_id and not args.name:
    print('❌ Specify either session_id or --name', file=sys.stderr)
    sys.exit(1)

  if args.session_id and args.name:
    print('❌ Cannot specify both session_id and --name', file=sys.stderr)
    sys.exit(1)

  try:
    # Resolve review app ID
    review_app_id, _ = await resolve_review_app_id(
      review_app_id=args.review_app_id, experiment_id=args.experiment_id
    )

    session_to_delete = None

    if args.session_id:
      # Get session by ID
      try:
        session_to_delete = await get_labeling_session(
          review_app_id=review_app_id, labeling_session_id=args.session_id
        )
      except Exception:
        print(f"❌ Session with ID '{args.session_id}' not found", file=sys.stderr)
        sys.exit(1)

    elif args.name:
      # Search for session by name
      session_to_delete = await get_session_by_name(
        review_app_id=review_app_id, session_name=args.name
      )

      if not session_to_delete:
        print(f"❌ Session with name '{args.name}' not found", file=sys.stderr)

        # Show available sessions
        sessions_response = await list_labeling_sessions(review_app_id=review_app_id)
        sessions = sessions_response.get('labeling_sessions', [])
        if sessions:
          print('Available sessions:', file=sys.stderr)
          for session in sessions:
            print(
              f'  - {session.get("name", "Unnamed")} '
              f'(ID: {session.get("labeling_session_id", "N/A")})',
              file=sys.stderr,
            )
        sys.exit(1)

    # Display session information
    session_name = session_to_delete.get('name', 'Unnamed')
    session_id = session_to_delete.get('labeling_session_id')
    mlflow_run_id = session_to_delete.get('mlflow_run_id')
    assigned_users = session_to_delete.get('assigned_users', [])
    schemas = [s['name'] for s in session_to_delete.get('labeling_schemas', [])]
    created_by = session_to_delete.get('created_by', 'Unknown')
    create_time = session_to_delete.get('create_time', 'Unknown')

    print('🗑️  **Session to be deleted:**')
    print(f'  Name: {session_name}')
    print(f'  ID: {session_id}')
    print(f'  MLflow Run ID: {mlflow_run_id}')
    print(f'  Assigned Users: {", ".join(assigned_users) if assigned_users else "None"}')
    print(f'  Schemas: {", ".join(schemas) if schemas else "None"}')
    print(f'  Created: {create_time} by {created_by}')

    if session_to_delete.get('description'):
      print(f'  Description: {session_to_delete.get("description")}')

    # Check for linked traces (if we have a way to check)
    # For now, we'll just warn about potential linked traces
    print('\n⚠️  **Important:**')
    print('  - This will delete the labeling session permanently')
    print('  - Any traces linked to this session will become unlinked')
    print('  - Any labeling work done in this session may be lost')
    print(f'  - The underlying MLflow run ({mlflow_run_id}) will remain')

    if args.dry_run:
      print('\n🔍 Dry run - no changes made')
      return

    # Confirmation
    if not args.force:
      confirmation_phrase = f'delete {session_name}'
      print('\n⚠️  **This action cannot be undone!**')
      print(f'To proceed, type: **{confirmation_phrase}**')
      user_input = input('Confirmation: ').strip()

      if user_input != confirmation_phrase:
        print('❌ Confirmation failed. No changes made.')
        return

    # Perform deletion
    await delete_labeling_session(review_app_id=review_app_id, labeling_session_id=session_id)

    # Success message
    print('\n✅ Successfully deleted labeling session:')
    print(f'  Name: {session_name}')
    print(f'  ID: {session_id}')

    print('\n💡 **Next steps:**')
    print(
      f'  - Check remaining sessions with: '
      f'uv run python tools/list_labeling_sessions.py {review_app_id}'
    )
    print('  - Create new sessions with: uv run python tools/create_labeling_session.py')

  except Exception as e:
    print(f'❌ Error: {str(e)}', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  asyncio.run(main())
