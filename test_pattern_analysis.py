#!/usr/bin/env python3
"""Test the pattern analysis to debug the permissions issue."""

import asyncio
import json
import sys
import os

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from utils.labeling_session_analysis import SMEInsightDiscovery
from utils.model_serving import ModelServingClient

async def test_pattern_analysis():
    """Test pattern analysis with mock data similar to the 'Correct response' session."""
    
    # Mock schemas matching the session
    schemas = [
        {
            'key': 'correctness',
            'name': 'Correctness',
            'schema_type': 'categorical',
            'categories': ['True', 'False'],
            'description': 'Is the response correct?'
        },
        {
            'key': 'comments',
            'name': 'Comments',
            'schema_type': 'text',
            'description': 'Additional comments'
        }
    ]
    
    # Mock items matching what you described (2 False with comments, 1 True)
    items = [
        {
            'state': 'COMPLETED',
            'source': {'trace_id': 'trace-001'},
            'labels': {
                'correctness': 'False',
                'comments': 'The agent says it cannot access query history due to permissions'
            }
        },
        {
            'state': 'COMPLETED',
            'source': {'trace_id': 'trace-002'},
            'labels': {
                'correctness': 'False',
                'comments': 'Again mentions permission limitations preventing access to data'
            }
        },
        {
            'state': 'COMPLETED',
            'source': {'trace_id': 'trace-003'},
            'labels': {
                'correctness': 'True',
                'comments': ''  # No comment on the True one
            }
        }
    ]
    
    # Create model client
    model_client = ModelServingClient()
    model_client.default_endpoint = 'databricks-dbrx-instruct'
    
    # Create insight discovery instance
    discovery = SMEInsightDiscovery(model_client)
    
    # First compute label distributions
    print("Computing label distributions...")
    label_distributions = discovery.compute_label_distributions(items, schemas)
    print("\nLabel Distributions:")
    print(json.dumps(label_distributions, indent=2))
    
    # Agent understanding (mock)
    agent_understanding = "Database performance troubleshooting agent being evaluated for correctness."
    
    # Now analyze patterns - this is the key method we're testing
    print("\n" + "="*60)
    print("Analyzing assessment patterns...")
    print("="*60)
    
    patterns = await discovery._analyze_assessment_patterns(
        items=items,
        schemas=schemas,
        agent_understanding=agent_understanding,
        label_distributions=label_distributions
    )
    
    print("\nPattern Analysis Result:")
    print(json.dumps(patterns, indent=2))
    
    # Show what data was sent to the LLM
    print("\n" + "="*60)
    print("DEBUG: What the analysis method extracted:")
    print("="*60)
    
    # Recreate what the method does to show the data
    negative_examples = []
    all_text_feedback = []
    
    for item in items:
        if item.get('state') == 'COMPLETED':
            labels = item.get('labels', {})
            
            # Find text feedback
            text_comment = None
            for schema_key, label_value in labels.items():
                schema = next((s for s in schemas if s.get('key') == schema_key), None)
                if schema and schema.get('schema_type') == 'text' and label_value:
                    text_comment = str(label_value)
                    all_text_feedback.append(text_comment)
            
            # Collect negative examples
            for schema_key, label_value in labels.items():
                dist = label_distributions.get(schema_key, {})
                if dist.get('type') == 'categorical' and str(label_value).lower() in ['false', 'no', 'incorrect']:
                    negative_examples.append({
                        'trace_id': item.get('source', {}).get('trace_id'),
                        'schema': schema_key,
                        'value': label_value,
                        'comment': text_comment
                    })
    
    print(f"\nNegative Examples Found: {len(negative_examples)}")
    print(json.dumps(negative_examples, indent=2))
    
    print(f"\nAll Text Feedback: {len(all_text_feedback)}")
    print(json.dumps(all_text_feedback, indent=2))
    
    # Check if permissions pattern was detected
    print("\n" + "="*60)
    print("VERIFICATION:")
    print("="*60)
    
    if patterns.get('main_pattern'):
        if 'permission' in patterns['main_pattern'].lower():
            print("✅ SUCCESS: Permissions pattern detected in main_pattern!")
        else:
            print("❌ FAILURE: Permissions pattern NOT detected in main_pattern")
            print(f"   Got: {patterns['main_pattern']}")
    
    if patterns.get('negative_reasons'):
        permissions_found = any('permission' in reason.lower() for reason in patterns['negative_reasons'])
        if permissions_found:
            print("✅ SUCCESS: Permissions mentioned in negative_reasons!")
        else:
            print("❌ FAILURE: Permissions NOT mentioned in negative_reasons")
            print(f"   Got: {patterns['negative_reasons']}")

if __name__ == "__main__":
    asyncio.run(test_pattern_analysis())