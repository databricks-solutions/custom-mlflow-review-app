#!/usr/bin/env python3
"""Tool to delete an assessment from a trace."""

import argparse
import sys
from typing import Optional

import mlflow
from mlflow.client import MlflowClient

from dotenv import load_dotenv

from server.utils.config import config
from server.utils.user_utils import user_utils

# Load environment variables
load_dotenv()
load_dotenv('.env.local')


def ensure_authentication():
    """Ensure user is authenticated."""
    try:
        user_utils.get_username()
    except Exception as e:
        print(f"Authentication failed: {e}", file=sys.stderr)
        sys.exit(1)


def get_experiment_id_from_config():
    """Get experiment ID from config."""
    return config.experiment_id


def delete_assessment(
    trace_id: str,
    assessment_id: str,
    experiment_id: Optional[str] = None,
) -> dict:
    """Delete an assessment from a trace.
    
    Args:
        trace_id: The trace ID to delete assessment from
        assessment_id: The assessment ID to delete
        experiment_id: Optional experiment ID to help locate the trace
        
    Returns:
        Dictionary with deletion status
    """
    ensure_authentication()
    client = MlflowClient()
    
    try:
        # Delete the assessment
        client.delete_assessment(trace_id, assessment_id)
        
        return {
            'success': True,
            'message': f'Successfully deleted assessment {assessment_id} from trace {trace_id}',
            'trace_id': trace_id,
            'assessment_id': assessment_id,
        }
    except Exception as e:
        error_msg = str(e)
        if 'not found' in error_msg.lower():
            return {
                'success': False,
                'error': f'Assessment {assessment_id} not found',
                'trace_id': trace_id,
                'assessment_id': assessment_id,
            }
        else:
            return {
                'success': False,
                'error': f'Failed to delete assessment: {error_msg}',
                'trace_id': trace_id,
                'assessment_id': assessment_id,
            }


def delete_all_assessments(trace_id: str, experiment_id: Optional[str] = None) -> dict:
    """Delete all assessments from a trace.
    
    Args:
        trace_id: The trace ID to delete all assessments from
        experiment_id: Optional experiment ID to help locate the trace
        
    Returns:
        Dictionary with deletion status
    """
    ensure_authentication()
    
    try:
        # First get the trace to find all assessments
        trace = mlflow.get_trace(trace_id)
        
        if not trace:
            return {
                'success': False,
                'error': f'Trace {trace_id} not found',
                'trace_id': trace_id,
            }
        
        # Get all assessments
        assessments = getattr(trace.info, 'assessments', [])
        
        if not assessments:
            return {
                'success': True,
                'message': f'No assessments found on trace {trace_id}',
                'trace_id': trace_id,
                'deleted_count': 0,
            }
        
        # Delete each assessment
        client = MlflowClient()
        deleted = []
        failed = []
        
        for assessment in assessments:
            # Get assessment ID - it might be in different places
            assessment_id = None
            if hasattr(assessment, 'id'):
                assessment_id = assessment.id
            elif hasattr(assessment, 'assessment_id'):
                assessment_id = assessment.assessment_id
            elif hasattr(assessment, 'source') and hasattr(assessment.source, 'source_id'):
                assessment_id = assessment.source.source_id
                
            if assessment_id:
                try:
                    client.delete_assessment(trace_id, assessment_id)
                    deleted.append({
                        'id': assessment_id,
                        'name': getattr(assessment, 'name', 'unknown'),
                    })
                except Exception as e:
                    failed.append({
                        'id': assessment_id,
                        'name': getattr(assessment, 'name', 'unknown'),
                        'error': str(e),
                    })
            else:
                # Try to identify assessment by name and value for logging
                name = getattr(assessment, 'name', 'unknown')
                failed.append({
                    'name': name,
                    'error': 'Could not find assessment ID',
                })
        
        return {
            'success': len(failed) == 0,
            'message': f'Deleted {len(deleted)} assessments from trace {trace_id}',
            'trace_id': trace_id,
            'deleted_count': len(deleted),
            'deleted': deleted,
            'failed': failed if failed else None,
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to delete assessments: {str(e)}',
            'trace_id': trace_id,
        }


def main():
    """Main function for CLI usage."""
    parser = argparse.ArgumentParser(
        description='Delete assessment(s) from a trace',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Delete a specific assessment
  %(prog)s --trace-id tr-abc123 --assessment-id asmt-xyz789
  
  # Delete all assessments from a trace
  %(prog)s --trace-id tr-abc123 --all
  
  # Delete with experiment context
  %(prog)s --trace-id tr-abc123 --all --experiment-id 12345
        ''',
    )
    
    parser.add_argument(
        '--trace-id',
        required=True,
        help='The trace ID to delete assessment(s) from',
    )
    
    parser.add_argument(
        '--assessment-id',
        help='The specific assessment ID to delete',
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Delete all assessments from the trace',
    )
    
    parser.add_argument(
        '--experiment-id',
        help='Optional experiment ID to help locate the trace',
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.all and not args.assessment_id:
        parser.error('Either --assessment-id or --all must be specified')
    
    if args.all and args.assessment_id:
        parser.error('Cannot specify both --assessment-id and --all')
    
    # Get experiment ID from config if not provided
    if not args.experiment_id:
        args.experiment_id = get_experiment_id_from_config()
    
    # Execute deletion
    if args.all:
        result = delete_all_assessments(
            trace_id=args.trace_id,
            experiment_id=args.experiment_id,
        )
    else:
        result = delete_assessment(
            trace_id=args.trace_id,
            assessment_id=args.assessment_id,
            experiment_id=args.experiment_id,
        )
    
    # Print result
    if result['success']:
        print(f"✅ {result['message']}")
        if 'deleted' in result and result['deleted']:
            print("\nDeleted assessments:")
            for item in result['deleted']:
                print(f"  - {item['name']} (ID: {item.get('id', 'N/A')})")
    else:
        print(f"❌ {result.get('error', 'Unknown error')}", file=sys.stderr)
        if 'failed' in result and result['failed']:
            print("\nFailed deletions:", file=sys.stderr)
            for item in result['failed']:
                print(f"  - {item.get('name', 'unknown')}: {item.get('error', 'unknown error')}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()