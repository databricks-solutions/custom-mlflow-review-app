"""Report Generator Module

Generates comprehensive markdown reports from analysis results.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates markdown reports from analysis results."""
    
    def __init__(self):
        """Initialize report generator."""
        self.logger = logging.getLogger(__name__)
    
    def generate_report(
        self,
        experiment_data: Dict[str, Any],
        discovery_result: Dict[str, Any],
        schemas: List[Dict[str, Any]]
    ) -> str:
        """Generate comprehensive markdown report.
        
        Args:
            experiment_data: Experiment and trace data
            discovery_result: Issue discovery results
            schemas: Generated evaluation schemas
            
        Returns:
            Markdown formatted report
        """
        
        report_sections = []
        
        # Header
        report_sections.append(self._generate_header(experiment_data))
        
        # Executive Summary
        report_sections.append(self._generate_executive_summary(
            experiment_data,
            discovery_result,
            schemas
        ))
        
        # Agent Understanding
        report_sections.append(self._generate_agent_section(discovery_result))
        
        # Quality Issues
        report_sections.append(self._generate_issues_section(discovery_result))
        
        # Recommended Schemas
        report_sections.append(self._generate_schemas_section(schemas))
        
        # Detailed Analysis
        report_sections.append(self._generate_detailed_analysis(discovery_result))
        
        # Footer
        report_sections.append(self._generate_footer())
        
        return '\n\n'.join(report_sections)
    
    def _generate_header(self, experiment_data: Dict[str, Any]) -> str:
        """Generate report header."""
        
        exp_info = experiment_data['experiment_info']
        
        return f"""# 🔬 Experiment Analysis Report

**Experiment:** {exp_info['name']} (ID: {exp_info['experiment_id']})
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Analysis Method:** Open-Ended Chain-of-Thought Discovery
**Traces Analyzed:** {experiment_data['total_traces']}"""
    
    def _generate_executive_summary(
        self,
        experiment_data: Dict[str, Any],
        discovery_result: Dict[str, Any],
        schemas: List[Dict[str, Any]]
    ) -> str:
        """Generate executive summary section."""
        
        issues = discovery_result['issues']
        critical_count = len([i for i in issues if i['severity'] == 'critical'])
        high_count = len([i for i in issues if i['severity'] == 'high'])
        
        # Count total affected traces (unique)
        all_affected_traces = set()
        for issue in issues:
            all_affected_traces.update(issue.get('all_trace_ids', []))
        
        return f"""## 📊 Executive Summary

- **Total Traces Analyzed:** {experiment_data['total_traces']}
- **Traces with Issues:** {len(all_affected_traces)} ({len(all_affected_traces)*100//max(experiment_data['total_traces'], 1)}%)
- **Unique Issue Types Found:** {len(issues)}
- **Critical Issues:** {critical_count}
- **High Priority Issues:** {high_count}
- **Evaluation Schemas Generated:** {len(schemas)}"""
    
    def _generate_agent_section(self, discovery_result: Dict[str, Any]) -> str:
        """Generate agent understanding section."""
        
        return f"""## 🤖 Agent Analysis

### What This Agent Does
{discovery_result['agent_understanding']}"""
    
    def _generate_issues_section(self, discovery_result: Dict[str, Any]) -> str:
        """Generate quality issues section."""
        
        issues = discovery_result['issues']
        
        if not issues:
            return "## 🚨 Quality Issues Found\n\nNo significant quality issues detected."
        
        sections = ["## 🚨 Quality Issues Found"]
        
        # Group by severity
        for severity in ['critical', 'high', 'medium', 'low']:
            severity_issues = [i for i in issues if i['severity'] == severity]
            
            if severity_issues:
                severity_emoji = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🟢'
                }[severity]
                
                sections.append(f"\n### {severity_emoji} {severity.title()} Severity Issues")
                
                for issue in severity_issues:
                    sections.append(f"""
#### {issue['title']}

- **Type:** `{issue['issue_type']}`
- **Affected Traces:** {issue['affected_traces']} out of {discovery_result['metadata']['total_traces_analyzed']}
- **Description:** {issue['description']}""")
                    
                    if issue.get('problem_snippets'):
                        sections.append("\n**Example Problems:**")
                        for snippet in issue['problem_snippets'][:2]:
                            sections.append(f"```\n{snippet}\n```")
        
        return '\n'.join(sections)
    
    def _generate_schemas_section(self, schemas: List[Dict[str, Any]]) -> str:
        """Generate recommended schemas section."""
        
        if not schemas:
            return "## 📋 Recommended Evaluation Schemas\n\nNo schemas generated."
        
        sections = ["## 📋 Recommended Evaluation Schemas"]
        
        # Separate by type
        feedback_schemas = [s for s in schemas if s['label_type'] == 'FEEDBACK']
        expectation_schemas = [s for s in schemas if s['label_type'] == 'EXPECTATION']
        
        if feedback_schemas:
            sections.append("\n### Human Feedback Schemas")
            sections.append("These schemas require human judgment and evaluation:")
            
            for schema in feedback_schemas[:5]:  # Top 5
                priority_badge = "🔥" if schema.get('priority_score', 0) > 75 else "📊"
                sections.append(f"""
{priority_badge} **{schema['name']}**
- **Type:** {schema['schema_type']}
- **Question:** {schema['description']}
- **Traces Affected:** {schema.get('affected_trace_count', 0)}
- **Priority Score:** {schema.get('priority_score', 0)}/100""")
        
        if expectation_schemas:
            sections.append("\n### Ground Truth Expectation Schemas")
            sections.append("These schemas capture correct/expected outputs:")
            
            for schema in expectation_schemas[:5]:  # Top 5
                priority_badge = "✅" if schema.get('priority_score', 0) > 75 else "📝"
                sections.append(f"""
{priority_badge} **{schema['name']}**
- **Type:** {schema['schema_type']}
- **Question:** {schema['description']}
- **Traces Affected:** {schema.get('affected_trace_count', 0)}
- **Priority Score:** {schema.get('priority_score', 0)}/100""")
        
        return '\n'.join(sections)
    
    def _generate_detailed_analysis(self, discovery_result: Dict[str, Any]) -> str:
        """Generate detailed analysis section."""
        
        sections = ["## 🔍 Detailed Analysis"]
        
        # Discovery Process
        sections.append("""
### Discovery Process

This analysis used an open-ended discovery approach:
1. **Agent Understanding**: First analyzed sample traces to understand the agent's purpose and expected behavior
2. **Issue Discovery**: Identified quality issues specific to this agent and domain without using predefined categories
3. **Comprehensive Analysis**: Systematically analyzed all traces for discovered issue patterns
4. **Schema Generation**: Created evaluation schemas tailored to the specific issues found""")
        
        # Issue Categories Discovered
        categories = discovery_result.get('discovered_categories', [])
        if categories:
            sections.append("\n### Discovered Issue Categories")
            sections.append("The following issue categories were discovered in the data:")
            
            for i, category in enumerate(categories[:5], 1):
                sections.append(f"""
{i}. **{category.get('issue_name', 'Unknown')}**
   - {category.get('description', 'No description')}
   - Why it matters: {category.get('why_it_matters', 'Impact unknown')}""")
        
        # Statistics
        issues = discovery_result['issues']
        if issues:
            total_traces = discovery_result['metadata']['total_traces_analyzed']
            
            sections.append("\n### Issue Distribution")
            sections.append(f"""
| Severity | Count | Percentage of Issues |
|----------|-------|---------------------|""")
            
            for severity in ['critical', 'high', 'medium', 'low']:
                count = len([i for i in issues if i['severity'] == severity])
                if count > 0:
                    percentage = count * 100 // max(len(issues), 1)
                    sections.append(f"| {severity.title()} | {count} | {percentage}% |")
        
        return '\n'.join(sections)
    
    def _generate_footer(self) -> str:
        """Generate report footer."""
        
        return """## 📝 Next Steps

1. **Review Generated Schemas**: Examine the suggested evaluation schemas and save the ones relevant to your needs
2. **Create Labeling Sessions**: Set up labeling sessions with the saved schemas for SME evaluation
3. **Assign SMEs**: Assign subject matter experts to review traces with identified issues
4. **Iterate**: Use feedback to improve the agent and re-run analysis periodically

---

*This report was generated using open-ended AI analysis with chain-of-thought reasoning. All issues and schemas are derived from the actual trace data without predefined categories.*"""