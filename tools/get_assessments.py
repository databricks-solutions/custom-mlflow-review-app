#!/usr/bin/env python3
"""Tool to get assessments from a trace."""

import argparse
import json
import sys
from typing import Optional

import mlflow

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


def get_assessments(trace_id: str, experiment_id: Optional[str] = None) -> dict:
    """Get all assessments from a trace.
    
    Args:
        trace_id: The trace ID to get assessments from
        experiment_id: Optional experiment ID to help locate the trace
        
    Returns:
        Dictionary with assessments data
    """
    ensure_authentication()
    
    try:
        # Get the trace
        trace = mlflow.get_trace(trace_id)
        
        if not trace:
            return {
                'success': False,
                'error': f'Trace {trace_id} not found',
                'trace_id': trace_id,
            }
        
        # Get all assessments
        assessments = getattr(trace.info, 'assessments', [])
        
        # Convert assessments to a readable format
        assessment_list = []
        for assessment in assessments:
            # Extract assessment data
            assessment_data = {
                'name': getattr(assessment, 'name', 'unknown'),
            }
            
            # Get assessment ID
            if hasattr(assessment, 'id'):
                assessment_data['id'] = assessment.id
            elif hasattr(assessment, 'assessment_id'):
                assessment_data['id'] = assessment.assessment_id
            elif hasattr(assessment, 'source') and hasattr(assessment.source, 'source_id'):
                assessment_data['id'] = assessment.source.source_id
            
            # Get value - could be in feedback or expectation
            if hasattr(assessment, 'feedback') and assessment.feedback:
                assessment_data['value'] = getattr(assessment.feedback, 'value', None)
                assessment_data['type'] = 'feedback'
                if hasattr(assessment.feedback, 'rationale'):
                    assessment_data['rationale'] = assessment.feedback.rationale
            elif hasattr(assessment, 'expectation') and assessment.expectation:
                assessment_data['value'] = getattr(assessment.expectation, 'value', None)
                assessment_data['type'] = 'expectation'
                if hasattr(assessment.expectation, 'rationale'):
                    assessment_data['rationale'] = assessment.expectation.rationale
            elif hasattr(assessment, 'value'):
                assessment_data['value'] = assessment.value
                assessment_data['type'] = 'unknown'
            
            # Get metadata
            if hasattr(assessment, 'metadata') and assessment.metadata:
                assessment_data['metadata'] = assessment.metadata
            
            # Get source information
            if hasattr(assessment, 'source') and assessment.source:
                source = assessment.source
                if hasattr(source, 'source_type') and hasattr(source, 'source_id'):
                    assessment_data['source'] = {
                        'type': source.source_type,
                        'id': source.source_id,
                    }
            
            # Get timestamp if available
            if hasattr(assessment, 'timestamp'):
                assessment_data['timestamp'] = assessment.timestamp
            
            assessment_list.append(assessment_data)
        
        return {
            'success': True,
            'trace_id': trace_id,
            'experiment_id': trace.info.experiment_id,
            'run_id': getattr(trace.info, 'run_id', None),
            'assessment_count': len(assessment_list),
            'assessments': assessment_list,
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to get assessments: {str(e)}',
            'trace_id': trace_id,
        }


def main():
    """Main function for CLI usage."""
    parser = argparse.ArgumentParser(
        description='Get assessments from a trace',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Get assessments from a trace
  %(prog)s --trace-id tr-abc123
  
  # Get assessments with JSON output
  %(prog)s --trace-id tr-abc123 --json
  
  # Get assessments with experiment context
  %(prog)s --trace-id tr-abc123 --experiment-id 12345
        ''',
    )
    
    parser.add_argument(
        '--trace-id',
        required=True,
        help='The trace ID to get assessments from',
    )
    
    parser.add_argument(
        '--experiment-id',
        help='Optional experiment ID to help locate the trace',
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON',
    )
    
    args = parser.parse_args()
    
    # Get experiment ID from config if not provided
    if not args.experiment_id:
        args.experiment_id = get_experiment_id_from_config()
    
    # Get assessments
    result = get_assessments(
        trace_id=args.trace_id,
        experiment_id=args.experiment_id,
    )
    
    # Output results
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result['success']:
            print(f"📊 Assessments for trace {result['trace_id']}")
            print(f"   Experiment: {result['experiment_id']}")
            if result['run_id']:
                print(f"   Run: {result['run_id']}")
            print(f"   Total assessments: {result['assessment_count']}")
            
            if result['assessments']:
                print("\n📝 Assessments:")
                for i, assessment in enumerate(result['assessments'], 1):
                    print(f"\n   {i}. {assessment['name']}")
                    if 'id' in assessment:
                        print(f"      ID: {assessment['id']}")
                    print(f"      Type: {assessment.get('type', 'unknown')}")
                    print(f"      Value: {assessment.get('value', 'N/A')}")
                    if 'rationale' in assessment:
                        print(f"      Rationale: {assessment['rationale']}")
                    if 'metadata' in assessment:
                        print(f"      Metadata: {json.dumps(assessment['metadata'], indent=10)}")
                    if 'source' in assessment:
                        print(f"      Source: {assessment['source']['type']} ({assessment['source']['id']})")
                    if 'timestamp' in assessment:
                        print(f"      Timestamp: {assessment['timestamp']}")
            else:
                print("\n   No assessments found")
        else:
            print(f"❌ {result.get('error', 'Unknown error')}", file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()