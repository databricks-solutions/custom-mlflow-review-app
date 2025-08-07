#!/usr/bin/env python3
"""Open labeling schemas page in browser for Databricks workspace or local app."""

import argparse
import subprocess
import sys


def prompt_user_choice() -> str:
  """Prompt user to choose between Databricks or local app.

  Returns:
      'databricks' or 'app' based on user choice
  """
  print('\n🔗 Where would you like to open the labeling schemas?', file=sys.stderr)
  print('  1) 🏢 MLflow Databricks', file=sys.stderr)
  print('  2) 💻 Custom App', file=sys.stderr)

  while True:
    try:
      choice = input('\nEnter your choice (1 or 2): ').strip()
      if choice == '1':
        return 'databricks'
      elif choice == '2':
        return 'app'
      else:
        print('Please enter 1 or 2', file=sys.stderr)
    except KeyboardInterrupt:
      print('\nCancelled by user', file=sys.stderr)
      sys.exit(1)


def main():
  """Open labeling schemas in browser."""
  parser = argparse.ArgumentParser(
    description='Open labeling schemas in Databricks or local app',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
    python open_labeling_schemas.py                    # Interactive choice
    python open_labeling_schemas.py --databricks       # Direct to Databricks
    python open_labeling_schemas.py --app              # Direct to local app
        """,
  )

  parser.add_argument('--databricks', action='store_true', help='Open in Databricks (skip prompt)')

  parser.add_argument('--app', action='store_true', help='Open in local app (skip prompt)')

  parser.add_argument('--no-open', action='store_true', help="Print URL only, don't open browser")

  args = parser.parse_args()

  # Determine choice
  if args.databricks and args.app:
    print('Error: Cannot specify both --databricks and --app', file=sys.stderr)
    return 1
  elif args.databricks:
    choice = 'databricks'
  elif args.app:
    choice = 'app'
  else:
    choice = prompt_user_choice()

  try:
    if choice == 'databricks':
      print('🏢 Opening MLflow Databricks labeling schemas...', file=sys.stderr)

      # Get experiment ID from config
      config_cmd = [sys.executable, 'server/utils/config.py']
      result = subprocess.run(config_cmd, capture_output=True, text=True, check=True)
      experiment_id = result.stdout.strip()

      # Generate Databricks URL
      databricks_cmd = [
        sys.executable,
        'tools/databricks_get_labeling_schemas_link.py',
        experiment_id,
      ]
      result = subprocess.run(databricks_cmd, capture_output=True, text=True, check=True)
      url = result.stdout.strip()

    else:  # app
      print('💻 Opening local app labeling schemas...', file=sys.stderr)

      # Generate local app URL
      app_cmd = [sys.executable, 'tools/app_get_labeling_schemas_link.py']
      result = subprocess.run(app_cmd, capture_output=True, text=True, check=True)
      url = result.stdout.strip()

    print(url)

    if not args.no_open:
      # Open in browser
      open_cmd = ['open', url]
      subprocess.run(open_cmd, check=True)
      print(f'✅ Opened {url}', file=sys.stderr)

  except subprocess.CalledProcessError as e:
    print(f'Error: {e.stderr if e.stderr else str(e)}', file=sys.stderr)
    return 1
  except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    return 1

  return 0


if __name__ == '__main__':
  exit(main())
