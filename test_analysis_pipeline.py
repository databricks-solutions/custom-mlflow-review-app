#!/usr/bin/env python
"""Test the new open-ended analysis pipeline."""

import asyncio
import json
from server.utils.experiment_analysis import ExperimentAnalyzer

async def test_pipeline():
    """Test the analysis pipeline with mock data."""
    
    # Create mock traces
    mock_traces = [
        {
            'info': {
                'trace_id': 'trace_001',
                'experiment_id': 'test_exp',
                'timestamp_ms': 1700000000000,
                'execution_time_ms': 1500,
                'status': 'OK',
            },
            'data': {
                'request': 'Help me analyze the customer database',
                'response': "I'll help you analyze the customer database. Let me run a query.",
                'spans': [
                    {
                        'span_id': 'span_001',
                        'name': 'sql_query',
                        'span_type': 'TOOL',
                        'status': 'ERROR',
                        'inputs': {'query': 'SELECT * FROM customers WHRE 1=1'},
                        'outputs': {'error': 'SQL syntax error: WHRE is not valid'},
                    }
                ]
            }
        },
        {
            'info': {
                'trace_id': 'trace_002',
                'experiment_id': 'test_exp',
                'timestamp_ms': 1700001000000,
                'execution_time_ms': 2000,
                'status': 'OK',
            },
            'data': {
                'request': 'Show me sales data',
                'response': 'Here is the sales data for last month.',
                'spans': [
                    {
                        'span_id': 'span_002',
                        'name': 'sql_query',
                        'span_type': 'TOOL',
                        'status': 'OK',
                        'inputs': {'query': 'SELECT * FROM sales WHERE month = 11'},
                        'outputs': {'result': '100 rows returned'},
                    }
                ]
            }
        },
        {
            'info': {
                'trace_id': 'trace_003',
                'experiment_id': 'test_exp',
                'timestamp_ms': 1700002000000,
                'execution_time_ms': 1200,
                'status': 'ERROR',
            },
            'data': {
                'request': 'Calculate revenue',
                'response': 'The total revenue is $1,234,567.',
                'spans': [
                    {
                        'span_id': 'span_003',
                        'name': 'sql_query',
                        'span_type': 'TOOL',
                        'status': 'ERROR',
                        'inputs': {'query': 'SELECT SUM(amount) FROM orders'},
                        'outputs': {'error': 'Connection timeout'},
                    }
                ]
            }
        },
        {
            'info': {
                'trace_id': 'trace_004',
                'experiment_id': 'test_exp',
                'timestamp_ms': 1700003000000,
                'execution_time_ms': 800,
                'status': 'OK',
            },
            'data': {
                'request': 'What is the customer count?',
                'response': 'We have approximately 5000 customers.',
                'spans': []  # No tool usage
            }
        },
        {
            'info': {
                'trace_id': 'trace_005',
                'experiment_id': 'test_exp',
                'timestamp_ms': 1700004000000,
                'execution_time_ms': 1100,
                'status': 'OK',
            },
            'data': {
                'request': 'List top products',
                'response': 'I cannot access the database right now.',
                'spans': [
                    {
                        'span_id': 'span_005',
                        'name': 'sql_query',
                        'span_type': 'TOOL',
                        'status': 'ERROR',
                        'inputs': {'query': 'SELECT * FROM products ORDER BY sales DESC'},
                        'outputs': {'error': 'Database unavailable'},
                    }
                ]
            }
        }
    ]
    
    # Mock experiment info
    mock_experiment_info = {
        'experiment_id': 'test_exp',
        'name': 'SQL Assistant Testing',
        'artifact_location': '/tmp/mlflow',
        'lifecycle_stage': 'active',
        'creation_time': 1700000000000,
        'last_update_time': 1700004000000,
        'tags': {}
    }
    
    # Create analyzer
    analyzer = ExperimentAnalyzer(model_endpoint='databricks-claude-sonnet-4')
    
    # Prepare data
    experiment_data = {
        'experiment_info': mock_experiment_info,
        'traces': mock_traces,
        'total_traces': len(mock_traces),
        'sample_size_requested': 5
    }
    
    # Run discovery
    print("🔬 Testing Open-Ended Issue Discovery Pipeline")
    print("=" * 60)
    
    print("\n📊 Input Data:")
    print(f"  - Experiment: {mock_experiment_info['name']}")
    print(f"  - Traces: {len(mock_traces)}")
    print(f"  - Trace IDs: {[t['info']['trace_id'] for t in mock_traces]}")
    
    print("\n🔍 Step 1: Discovering issues...")
    discovery_result = await analyzer.issue_discovery.discover_issues(
        mock_traces,
        mock_experiment_info
    )
    
    print("\n✅ Discovery Results:")
    print(f"  - Agent Understanding: {discovery_result['agent_understanding'][:100]}...")
    print(f"  - Discovered Categories: {len(discovery_result.get('discovered_categories', []))}")
    print(f"  - Total Issues Found: {len(discovery_result['issues'])}")
    
    print("\n📋 Issues with ALL Trace IDs:")
    for issue in discovery_result['issues']:
        print(f"\n  Issue: {issue['title']}")
        print(f"    - Severity: {issue['severity']}")
        print(f"    - Affected Traces: {issue['affected_traces']}")
        print(f"    - ALL Trace IDs: {issue.get('all_trace_ids', [])}")
        print(f"    - Trace ID Count Match: {len(issue.get('all_trace_ids', [])) == issue['affected_traces']}")
    
    print("\n🔧 Step 2: Generating schemas...")
    schemas = analyzer.schema_generator.generate_schemas_for_issues(
        discovery_result['issues'],
        discovery_result['agent_understanding']
    )
    
    print(f"\n✅ Generated {len(schemas)} Schemas:")
    for schema in schemas[:3]:  # Show first 3
        print(f"\n  Schema: {schema['name']}")
        print(f"    - Type: {schema['label_type']} / {schema['schema_type']}")
        print(f"    - Question: {schema['description']}")
        print(f"    - Priority: {schema['priority_score']}")
        print(f"    - Affected Traces: {schema['affected_trace_count']}")
    
    print("\n✅ Validation Results:")
    print(f"  - All issues have trace IDs: {all(issue.get('all_trace_ids') for issue in discovery_result['issues'])}")
    print(f"  - Schema descriptions are clean: {all('Problem seen:' not in s['description'] for s in schemas)}")
    print(f"  - Schemas have label types: {all('label_type' in s for s in schemas)}")
    
    print("\n🎉 Pipeline test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_pipeline())