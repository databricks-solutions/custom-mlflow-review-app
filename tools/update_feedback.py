#!/usr/bin/env python3
"""Update feedback on a trace using MLflow SDK."""

import argparse
import sys
from pathlib import Path

# Add server directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

from utils.mlflow_utils import update_feedback


def main():
    parser = argparse.ArgumentParser(
        description="Update existing feedback on a trace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update feedback value
  python tools/update_feedback.py tr-abc123 a-def456 "Updated value"

  # Update feedback with rationale
  python tools/update_feedback.py tr-abc123 a-def456 "Updated value" --rationale "New reasoning"

  # Update feedback with username
  python tools/update_feedback.py tr-abc123 a-def456 "Updated value" --username "user@example.com"
        """,
    )

    parser.add_argument("trace_id", help="The trace ID to update feedback on")
    parser.add_argument("assessment_id", help="The assessment ID to update")
    parser.add_argument("value", help="The new feedback value")
    parser.add_argument(
        "--rationale", help="Optional rationale for the feedback update"
    )
    parser.add_argument(
        "--username", default="cli_user", help="Username providing the feedback (default: cli_user)"
    )

    args = parser.parse_args()

    try:
        print(f"Updating feedback on trace {args.trace_id[:8]}...")
        print(f"Assessment ID: {args.assessment_id}")
        print(f"New value: {args.value}")
        if args.rationale:
            print(f"Rationale: {args.rationale}")
        print(f"Username: {args.username}")

        result = update_feedback(
            trace_id=args.trace_id,
            assessment_id=args.assessment_id,
            value=args.value,
            username=args.username,
            rationale=args.rationale,
        )

        print(f"\n✅ {result['message']}")
        print(f"Assessment ID: {result['assessment_id']}")

    except Exception as e:
        print(f"❌ Error updating feedback: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()