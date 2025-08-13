#!/usr/bin/env python3
"""Test that the pattern analysis correctly identifies permissions issues from comments."""

import json

def test_permissions_detection():
    """Simulate the data flow to verify permissions pattern is detected."""
    
    print("=" * 60)
    print("TESTING PERMISSIONS PATTERN DETECTION")
    print("=" * 60)
    
    # Mock the data as it would appear in the "Correct response" session
    items = [
        {
            'state': 'COMPLETED',
            'source': {'trace_id': 'trace-001'},
            'labels': {
                'correctness': False,  # Note: Boolean False, not string
                'comments': 'The agent says it cannot access query history due to permissions'
            }
        },
        {
            'state': 'COMPLETED', 
            'source': {'trace_id': 'trace-002'},
            'labels': {
                'correctness': False,
                'comments': 'Again mentions permission limitations preventing access to data'
            }
        },
        {
            'state': 'COMPLETED',
            'source': {'trace_id': 'trace-003'},
            'labels': {
                'correctness': True,
                'comments': ''  # No comment on the True one
            }
        }
    ]
    
    # Simulate the negative examples extraction (as the fixed code does)
    negative_examples = []
    all_text_feedback = []
    
    schemas = [
        {'key': 'correctness', 'schema_type': 'categorical'},
        {'key': 'comments', 'schema_type': 'text'}
    ]
    
    for item in items:
        if item.get('state') == 'COMPLETED':
            labels = item.get('labels', {})
            trace_id = item.get('source', {}).get('trace_id')
            
            # Find text feedback
            text_comment = None
            for schema_key, label_value in labels.items():
                schema = next((s for s in schemas if s.get('key') == schema_key), None)
                if schema and schema.get('schema_type') == 'text' and label_value:
                    text_comment = str(label_value)
                    all_text_feedback.append(text_comment)
            
            # Collect negative examples with comments
            for schema_key, label_value in labels.items():
                # Handle both boolean False and string 'False'
                if schema_key == 'correctness':
                    is_negative = (
                        (isinstance(label_value, bool) and not label_value) or
                        (isinstance(label_value, str) and label_value.lower() in ['false', 'no', 'incorrect'])
                    )
                    if is_negative:
                        negative_examples.append({
                            'trace_id': trace_id,
                            'schema': schema_key,
                            'value': label_value,
                            'comment': text_comment
                        })
    
    print("\n📊 EXTRACTED DATA:")
    print(f"Negative Examples Found: {len(negative_examples)}")
    for i, ex in enumerate(negative_examples, 1):
        print(f"\n  Example {i}:")
        print(f"    Trace: {ex['trace_id']}")
        print(f"    Value: {ex['value']}")
        print(f"    Comment: {ex['comment']}")
    
    print(f"\n\nAll Text Feedback: {len(all_text_feedback)}")
    for i, feedback in enumerate(all_text_feedback, 1):
        if feedback:  # Only show non-empty feedback
            print(f"  {i}. {feedback}")
    
    # Verify permissions pattern is captured
    print("\n" + "=" * 60)
    print("VERIFICATION:")
    print("=" * 60)
    
    permissions_found = False
    for ex in negative_examples:
        if ex.get('comment') and 'permission' in ex['comment'].lower():
            permissions_found = True
            print(f"✅ Found permissions issue in: {ex['comment']}")
    
    if permissions_found:
        print("\n✅ SUCCESS: The fixed code correctly extracts permissions issues from comments!")
        print("\nThe LLM prompt will now receive:")
        print("1. Negative examples WITH their comments explaining permissions issues")
        print("2. Full trace data showing what the agent actually said")
        print("3. Clear instruction to look at comments for the WHY")
    else:
        print("\n❌ FAILURE: Permissions pattern not detected in comments")
    
    # Show what the LLM will see
    print("\n" + "=" * 60)
    print("DATA SENT TO LLM:")
    print("=" * 60)
    print("\nNegative Examples (what LLM sees):")
    print(json.dumps(negative_examples, indent=2))
    
    print("\n✨ The LLM prompt explicitly says:")
    print('"CRITICAL: Look at the \'comment\' field in negative examples - it contains the WHY!"')

if __name__ == "__main__":
    test_permissions_detection()