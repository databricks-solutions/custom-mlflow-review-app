#!/usr/bin/env python3
"""Set assigned users for a labeling session.

This tool provides a simple interface to replace all assigned users for a labeling session.
It's a convenience wrapper around the update_labeling_session tool.

Category: labeling
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from server.utils.labeling_sessions_utils import get_labeling_session, update_labeling_session
from tools.utils.review_app_resolver import resolve_review_app_id


async def main():
  parser = argparse.ArgumentParser(
    description='Set assigned users for a labeling session',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # Set single user (uses current experiment)
  python set_assigned_users.py session_id user1@example.com

  # Set with specific review app ID
  python set_assigned_users.py review_app_id session_id user1@example.com user2@example.com user3@example.com

  # Set with specific experiment ID
  python set_assigned_users.py --experiment-id exp123 session_id

  # Clear all assigned users (no additional arguments)
  python set_assigned_users.py session_id
        """,
  )

  # For backwards compatibility, keep positional argument but make it optional
  parser.add_argument(
    'review_app_id', nargs='?', help='Review app ID (optional, defaults to current experiment)'
  )
  parser.add_argument('--experiment-id', help='Experiment ID (defaults to config experiment_id)')
  parser.add_argument('session_id', help='Labeling session ID to update')
  parser.add_argument(
    'users', nargs='*', help='Email addresses of users to assign (space-separated)'
  )
  parser.add_argument(
    '--dry-run', action='store_true', help='Show what would be updated without actually updating'
  )

  args = parser.parse_args()

  try:
    # Resolve review app ID
    review_app_id, _ = await resolve_review_app_id(
      review_app_id=args.review_app_id, experiment_id=args.experiment_id
    )

    # Get current session info to show before/after
    try:
      current_session = await get_labeling_session(
        review_app_id=review_app_id, labeling_session_id=args.session_id
      )
      current_users = current_session.get('assigned_users', [])
      session_name = current_session.get('name', 'Unknown Session')

      print(f'📋 **Session: {session_name}**')
      print(f'  ID: {args.session_id}')
      print(f'  Current assigned users: {", ".join(current_users) if current_users else "None"}')

    except Exception as e:
      print(f'⚠️  Warning: Could not fetch current session info: {e}')
      session_name = 'Unknown Session'
      current_users = []

    # Validate users list
    new_users = args.users if args.users else []

    # Show what will change
    if args.dry_run:
      print('\n🔍 **Dry Run - No changes will be made:**')
      print(f'  Would set assigned users to: {", ".join(new_users) if new_users else "None"}')
      return

    print('\n🔄 **Updating assigned users...**')
    print(f'  Setting assigned users to: {", ".join(new_users) if new_users else "None"}')

    # Use the update_labeling_session function with users parameter
    try:
      updated_session = await update_labeling_session(
        review_app_id=review_app_id,
        labeling_session_id=args.session_id,
        assigned_users=new_users,
      )

      print(f"✅ Successfully updated session '{session_name}':")
      print(f'  Assigned users: {", ".join(new_users) if new_users else "None"}')

    except Exception as e:
      print(f'❌ Failed to update session: {e}')
      sys.exit(1)

  except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)


if __name__ == '__main__':
  asyncio.run(main())
