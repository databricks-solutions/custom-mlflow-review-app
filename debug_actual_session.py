#!/usr/bin/env python3
"""Debug the actual session to see what's happening."""

import asyncio
import json
import sys
import os

sys.path.insert(0, 'server')

from utils.labeling_session_analysis import SMEInsightDiscovery
from utils.model_serving import ModelServingClient

async def debug_session():
    """Debug why the session isn't showing permissions pattern."""
    
    # Create mock data matching YOUR actual session
    schemas = [
        {
            'key': 'correct',
            'name': 'Correct',
            'schema_type': 'categorical',
            'categories': ['True', 'False'],
            'label_type': 'FEEDBACK'
        },
        {
            'key': 'comment',
            'name': 'Comment',
            'schema_type': 'text',
            'label_type': 'FEEDBACK'
        }
    ]
    
    # Your actual session data (2 False with permission comments, 1 True)
    items = [
        {
            'state': 'COMPLETED',
            'source': {'trace_id': 'tr-warehouse-list'},
            'labels': {
                'correct': False,
                'comment': 'The agent says it cannot access query history due to permissions'
            }
        },
        {
            'state': 'COMPLETED',
            'source': {'trace_id': 'tr-performance-issue'},
            'labels': {
                'correct': False,
                'comment': 'Again mentions permission limitations preventing access to data'
            }
        },
        {
            'state': 'COMPLETED',
            'source': {'trace_id': 'tr-optimization'},
            'labels': {
                'correct': True,
                'comment': ''
            }
        }
    ]
    
    # Mock traces
    traces = [
        {
            'info': {'trace_id': 'tr-warehouse-list'},
            'data': {
                'request': 'List all available SQL warehouses',
                'response': 'I cannot access the warehouse list due to permission restrictions...'
            }
        },
        {
            'info': {'trace_id': 'tr-performance-issue'},
            'data': {
                'request': 'Why is my query running slow?',
                'response': 'I am unable to access query history due to permission limitations...'
            }
        },
        {
            'info': {'trace_id': 'tr-optimization'},
            'data': {
                'request': 'How do I optimize a query?',
                'response': 'Here are some optimization strategies: 1) Use indexes...'
            }
        }
    ]
    
    # Initialize discovery
    model_client = ModelServingClient()
    model_client.default_endpoint = 'databricks-dbrx-instruct'
    discovery = SMEInsightDiscovery(model_client)
    
    # Step 1: Compute distributions
    print("=" * 60)
    print("STEP 1: Computing Label Distributions")
    print("=" * 60)
    distributions = discovery.compute_label_distributions(items, schemas)
    print(json.dumps(distributions, indent=2))
    
    # Step 2: Check what gets extracted
    print("\n" + "=" * 60)
    print("STEP 2: Extracting Negative Examples & Comments")
    print("=" * 60)
    
    negative_examples = []
    all_text_feedback = []
    
    # Recreate the extraction logic
    trace_map = {t['info']['trace_id']: t for t in traces}
    
    for item in items:
        if item.get('state') == 'COMPLETED':
            labels = item.get('labels', {})
            trace_id = item.get('source', {}).get('trace_id')
            
            # Find text comment
            text_comment = None
            for schema_key, label_value in labels.items():
                schema = next((s for s in schemas if s.get('key') == schema_key), None)
                if schema and schema.get('schema_type') == 'text' and label_value:
                    text_comment = str(label_value)
                    all_text_feedback.append(text_comment)
            
            # Check for negative values
            for schema_key, label_value in labels.items():
                schema = next((s for s in schemas if s.get('key') == schema_key), None)
                dist = distributions.get(schema_key, {})
                
                # Debug the condition check
                print(f"\nChecking {schema_key}={label_value}")
                print(f"  Schema type: {dist.get('type')}")
                print(f"  Is False?: {str(label_value).lower() in ['false', 'no', 'incorrect']}")
                print(f"  Value type: {type(label_value)}")
                
                if dist.get('type') == 'categorical':
                    # Handle both boolean and string False
                    is_negative = (
                        (isinstance(label_value, bool) and not label_value) or
                        (isinstance(label_value, str) and str(label_value).lower() in ['false', 'no', 'incorrect'])
                    )
                    
                    if is_negative:
                        negative_examples.append({
                            'trace_id': trace_id,
                            'schema': schema_key,
                            'value': label_value,
                            'comment': text_comment,
                            'trace_data': trace_map.get(trace_id)
                        })
                        print(f"  ✅ Added to negative examples with comment: {text_comment}")
    
    print(f"\n\nFINAL RESULTS:")
    print(f"Negative examples found: {len(negative_examples)}")
    print(f"Text feedback collected: {len(all_text_feedback)}")
    
    print("\n" + "=" * 60)
    print("NEGATIVE EXAMPLES WITH COMMENTS:")
    print("=" * 60)
    for ex in negative_examples:
        print(f"\nTrace: {ex['trace_id']}")
        print(f"Value: {ex['value']}")
        print(f"Comment: {ex['comment']}")
        if ex.get('trace_data'):
            print(f"Response snippet: {str(ex['trace_data']['data']['response'])[:100]}...")
    
    # Verify permissions mentioned
    print("\n" + "=" * 60)
    print("VERIFICATION:")
    print("=" * 60)
    
    permissions_count = sum(1 for ex in negative_examples if ex.get('comment') and 'permission' in ex['comment'].lower())
    print(f"Negative examples with 'permission' in comment: {permissions_count}/{len(negative_examples)}")
    
    if permissions_count > 0:
        print("✅ Permissions pattern SHOULD be detected!")
    else:
        print("❌ No permissions pattern found in comments")

if __name__ == "__main__":
    asyncio.run(debug_session())