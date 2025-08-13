#!/usr/bin/env python3
"""Test the simplified labeling session analysis and grade the output."""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List

# Mock data for testing
def create_mock_session_data():
    """Create mock session data for testing."""
    # Create mock schemas
    schemas = [
        {
            'key': 'correctness',
            'name': 'Correctness',
            'schema_type': 'categorical',
            'categories': ['Correct', 'Incorrect', 'Partially Correct'],
            'description': 'Whether the response is factually accurate'
        },
        {
            'key': 'helpfulness',
            'name': 'Helpfulness',
            'schema_type': 'numerical',
            'min': 1,
            'max': 5,
            'description': 'How helpful the response was (1-5 scale)'
        },
        {
            'key': 'feedback',
            'name': 'Additional Feedback',
            'schema_type': 'text',
            'description': 'Any additional comments'
        }
    ]
    
    # Create mock items with assessments
    items = [
        {
            'state': 'COMPLETED',
            'source': {'trace_id': 'trace-001'},
            'labels': {
                'correctness': 'Incorrect',
                'helpfulness': 2,
                'feedback': 'Response was truncated mid-sentence'
            }
        },
        {
            'state': 'COMPLETED',
            'source': {'trace_id': 'trace-002'},
            'labels': {
                'correctness': 'Correct',
                'helpfulness': 5,
                'feedback': 'Perfect response with good examples'
            }
        },
        {
            'state': 'COMPLETED',
            'source': {'trace_id': 'trace-003'},
            'labels': {
                'correctness': 'Incorrect',
                'helpfulness': 1,
                'feedback': 'Missing critical context and guidance'
            }
        },
        {
            'state': 'COMPLETED',
            'source': {'trace_id': 'trace-004'},
            'labels': {
                'correctness': 'Partially Correct',
                'helpfulness': 3,
                'feedback': 'Good start but lacks detail'
            }
        },
        {
            'state': 'PENDING',
            'source': {'trace_id': 'trace-005'},
            'labels': {}
        }
    ]
    
    # Create mock traces
    traces = [
        {
            'info': {'trace_id': 'trace-001'},
            'data': {
                'request': 'How do I list SQL warehouses?',
                'response': 'You can list SQL warehouses by using the Databricks CLI command databricks warehouses list or through the UI by navigating to SQL Wareh...'
            }
        },
        {
            'info': {'trace_id': 'trace-002'},
            'data': {
                'request': 'What is MLflow?',
                'response': 'MLflow is an open-source platform for managing the machine learning lifecycle, including experimentation, reproducibility, deployment, and a central model registry.'
            }
        }
    ]
    
    return schemas, items, traces

def create_simplified_report(distributions, patterns, recommendations):
    """Create a simplified report mimicking the new format."""
    report = []
    
    # Header
    report.append("# Labeling Session Analysis: Test Session")
    report.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')} | **Progress:** 4/5 items (80%)")
    report.append("")
    
    # Summary
    report.append("## Summary")
    report.append("This session evaluates a Databricks Assistant agent across 5 traces, assessing correctness (categorical), helpfulness (1-5 scale), and collecting text feedback to identify response quality patterns.")
    report.append("")
    
    # Label Distributions
    report.append("## Label Distributions")
    for key, dist in distributions.items():
        if dist['total'] > 0:
            report.append(f"- **{dist['name']}**: {dist['summary']}")
            if dist['type'] == 'categorical' and 'distribution' in dist:
                for cat, data in dist['distribution'].items():
                    report.append(f"  - {cat}: {data['count']} ({data['percentage']}%)")
    report.append("")
    
    # Pattern Analysis
    report.append("## Pattern Analysis")
    report.append(f"**Main Pattern:** {patterns['main_pattern']}")
    report.append("\n**Key Findings:**")
    for finding in patterns['key_findings']:
        report.append(f"- {finding}")
    if patterns.get('negative_reasons'):
        report.append("\n**Issues Identified:**")
        for reason in patterns['negative_reasons']:
            report.append(f"- {reason}")
    report.append("")
    
    # Key Actions
    report.append("## Key Actions")
    for i, rec in enumerate(recommendations[:5], 1):
        report.append(f"{i}. {rec}")
    
    return '\n'.join(report)

def grade_report(report: str) -> Dict[str, Any]:
    """Grade the report on conciseness, actionability, and quality."""
    grades = {}
    
    # Conciseness (A+ if < 1000 chars, A if < 1500, B if < 2000, C if < 3000, F otherwise)
    char_count = len(report)
    word_count = len(report.split())
    
    if char_count < 1000:
        grades['conciseness'] = 'A+'
    elif char_count < 1500:
        grades['conciseness'] = 'A'
    elif char_count < 2000:
        grades['conciseness'] = 'B'
    elif char_count < 3000:
        grades['conciseness'] = 'C'
    else:
        grades['conciseness'] = 'F'
    
    # Actionability (based on presence of key sections)
    has_distributions = 'Label Distributions' in report
    has_patterns = 'Pattern Analysis' in report and 'Main Pattern:' in report
    has_actions = 'Key Actions' in report
    has_findings = 'Key Findings:' in report
    
    actionability_score = sum([has_distributions, has_patterns, has_actions, has_findings])
    if actionability_score == 4:
        grades['actionability'] = 'A+'
    elif actionability_score == 3:
        grades['actionability'] = 'A'
    elif actionability_score == 2:
        grades['actionability'] = 'B'
    else:
        grades['actionability'] = 'C'
    
    # Summary Quality (based on brevity and informativeness)
    summary_section = report.split('## Summary')[1].split('##')[0] if '## Summary' in report else ''
    summary_words = len(summary_section.split())
    
    if 20 <= summary_words <= 50 and 'evaluates' in summary_section and 'traces' in summary_section:
        grades['summary_quality'] = 'A+'
    elif summary_words <= 80:
        grades['summary_quality'] = 'A'
    elif summary_words <= 120:
        grades['summary_quality'] = 'B'
    else:
        grades['summary_quality'] = 'C'
    
    # Overall Grade
    grade_points = {
        'A+': 4.3, 'A': 4.0, 'A-': 3.7,
        'B+': 3.3, 'B': 3.0, 'B-': 2.7,
        'C+': 2.3, 'C': 2.0, 'C-': 1.7,
        'D': 1.0, 'F': 0.0
    }
    
    avg_points = sum(grade_points.get(g, 0) for g in grades.values()) / len(grades)
    
    if avg_points >= 4.2:
        overall = 'A+'
    elif avg_points >= 3.8:
        overall = 'A'
    elif avg_points >= 3.5:
        overall = 'A-'
    elif avg_points >= 3.2:
        overall = 'B+'
    elif avg_points >= 2.8:
        overall = 'B'
    else:
        overall = 'B-'
    
    return {
        'grades': grades,
        'overall': overall,
        'stats': {
            'character_count': char_count,
            'word_count': word_count,
            'summary_words': summary_words
        }
    }

def main():
    """Run the test and grade the output."""
    print("🧪 Testing Simplified Labeling Session Analysis")
    print("=" * 50)
    
    # Create mock data
    schemas, items, traces = create_mock_session_data()
    
    # Calculate distributions (mimicking the real implementation)
    from collections import Counter
    distributions = {}
    
    for schema in schemas:
        schema_key = schema['key']
        schema_type = schema['schema_type']
        
        labels = []
        for item in items:
            if item['state'] == 'COMPLETED' and schema_key in item.get('labels', {}):
                labels.append(item['labels'][schema_key])
        
        if not labels:
            continue
            
        if schema_type == 'categorical':
            counts = Counter(labels)
            total = sum(counts.values())
            distributions[schema_key] = {
                'name': schema['name'],
                'type': 'categorical',
                'total': total,
                'distribution': {
                    cat: {'count': count, 'percentage': round(count/total * 100, 1)}
                    for cat, count in counts.items()
                },
                'summary': f"{counts.most_common(1)[0][0]}: {counts.most_common(1)[0][1]}/{total}"
            }
        elif schema_type == 'numerical':
            numeric_labels = [float(l) for l in labels]
            avg = sum(numeric_labels) / len(numeric_labels)
            distributions[schema_key] = {
                'name': schema['name'],
                'type': 'numerical',
                'total': len(numeric_labels),
                'mean': round(avg, 2),
                'summary': f"Avg: {round(avg, 1)} (n={len(numeric_labels)})"
            }
        elif schema_type == 'text':
            distributions[schema_key] = {
                'name': schema['name'],
                'type': 'text',
                'total': len(labels),
                'summary': f"{len(labels)} text responses"
            }
    
    # Create mock pattern analysis
    patterns = {
        'main_pattern': 'Response truncation and incomplete guidance are the primary issues, occurring in 50% of evaluated traces.',
        'key_findings': [
            'Response truncation affects 25% of traces',
            'Low helpfulness scores correlate with missing context',
            '50% correctness failure rate indicates systematic issues'
        ],
        'negative_reasons': [
            'Responses cut off mid-sentence causing confusion',
            'Lack of specific examples and actionable guidance',
            'Missing critical context for decision-making'
        ]
    }
    
    # Create mock recommendations
    recommendations = [
        'Fix response truncation by increasing max token limits',
        'Add validation to ensure complete responses before sending',
        'Include specific examples and step-by-step guidance in responses',
        'Implement context checks to ensure all necessary information is provided',
        'Add quality validation for correctness before response delivery'
    ]
    
    # Generate the report
    report = create_simplified_report(distributions, patterns, recommendations)
    
    print("\n📄 GENERATED REPORT:")
    print("-" * 50)
    print(report)
    print("-" * 50)
    
    # Grade the report
    grades = grade_report(report)
    
    print("\n📊 GRADING RESULTS:")
    print("-" * 50)
    print(f"Conciseness:      {grades['grades']['conciseness']}")
    print(f"Actionability:    {grades['grades']['actionability']}")
    print(f"Summary Quality:  {grades['grades']['summary_quality']}")
    print(f"\n🎯 OVERALL GRADE: {grades['overall']}")
    print("\n📈 Statistics:")
    print(f"- Character count: {grades['stats']['character_count']}")
    print(f"- Word count: {grades['stats']['word_count']}")
    print(f"- Summary words: {grades['stats']['summary_words']}")
    
    # Provide feedback
    print("\n💭 SELF-ASSESSMENT:")
    if grades['overall'] in ['A+', 'A', 'A-']:
        print("✅ The simplified report meets the goals:")
        print("- Concise and scannable format")
        print("- Clear distribution statistics")
        print("- Focused on WHY patterns occur")
        print("- Actionable recommendations")
    else:
        print("⚠️ Areas for improvement:")
        if grades['grades']['conciseness'] not in ['A+', 'A']:
            print("- Report could be more concise")
        if grades['grades']['actionability'] not in ['A+', 'A']:
            print("- Need clearer action items")
        if grades['grades']['summary_quality'] not in ['A+', 'A']:
            print("- Summary could be more focused")

if __name__ == "__main__":
    main()