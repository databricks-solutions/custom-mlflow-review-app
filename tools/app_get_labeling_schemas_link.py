#!/usr/bin/env python3
"""Tool to generate labeling schemas link for the local development app."""

import argparse
import os


def get_app_labeling_schemas_link() -> str:
  """Generate a local development app labeling schemas link.

  Returns:
      Complete URL to the local labeling schemas page

  Example:
      http://localhost:5173/labeling-schemas
  """
  return 'http://localhost:5173/labeling-schemas'


def main():
  """Generate local app labeling schemas link."""
  parser = argparse.ArgumentParser(
    description='Generate local app labeling schemas link',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
    python app_get_labeling_schemas_link.py

    # Open directly in browser (macOS)
    open $(python app_get_labeling_schemas_link.py)
        """,
  )

  parser.add_argument(
    '--help-detailed', action='store_true', help='Show detailed help with examples'
  )

  if '--help-detailed' in os.sys.argv:
    print("""
Local App Labeling Schemas Link Generator

This tool generates direct links to the local development labeling schemas
management interface.

URL Structure:
    http://localhost:5173/labeling-schemas

Usage Examples:
    # Generate link for local labeling schemas
    python app_get_labeling_schemas_link.py

    # Open link directly in browser (macOS)
    open $(python app_get_labeling_schemas_link.py)

Integration Notes:
    - Use this tool to quickly access the local development schemas interface
    - Link provides access to create, edit, and manage labeling schemas locally
    - Requires the development server to be running on localhost:5173
    - This is the local development version of the schemas management interface
        """)
    return

  try:
    link = get_app_labeling_schemas_link()
    print(link)
  except Exception as e:
    print(f'Error: {e}')
    return 1

  return 0


if __name__ == '__main__':
  exit(main())
