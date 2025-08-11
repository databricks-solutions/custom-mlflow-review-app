#!/usr/bin/env python3
"""Get current user and workspace information."""

import argparse
import inspect
import json
import sys

from server.utils.user_utils import user_utils


def main():
  """Get workspace information."""
  # Extract description from the utility function's docstring
  func_doc = inspect.getdoc(user_utils.get_user_workspace_info)
  description = (
    func_doc.split('\n')[0] if func_doc else 'Get current user and workspace information'
  )

  parser = argparse.ArgumentParser(description=description)
  parser.parse_args()

  try:
    result = user_utils.get_user_workspace_info()
    print(json.dumps(result, indent=2))
  except Exception as e:
    print(f'❌ Error: {str(e)}', file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
  main()
