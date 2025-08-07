#!/usr/bin/env python3
"""Unified CLI tool for MLflow Review App operations.

This tool provides a centralized interface to all MLflow Review App tools
with command discovery, help, and unified execution.
"""

import argparse
import asyncio
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()
load_dotenv('.env.local')


class ToolInfo:
  """Information about a CLI tool."""

  def __init__(self, name: str, path: Path, description: str, category: str):
    self.name = name
    self.path = path
    self.description = description
    self.category = category


class UnifiedCLI:
  """Unified CLI tool for MLflow Review App operations."""

  def __init__(self):
    self.tools_dir = project_root / 'tools'
    self.tools = self._discover_tools()

  def _discover_tools(self) -> Dict[str, ToolInfo]:
    """Discover all available tools in the tools directory."""
    tools = {}

    if not self.tools_dir.exists():
      return tools

    for tool_file in self.tools_dir.glob('*.py'):
      if tool_file.name.startswith('__'):
        continue

      tool_name = tool_file.stem
      description, category = self._extract_tool_info(tool_file)

      tools[tool_name] = ToolInfo(
        name=tool_name, path=tool_file, description=description, category=category
      )

    return tools

  def _extract_tool_info(self, tool_file: Path) -> tuple[str, str]:
    """Extract description and category from tool file."""
    try:
      with open(tool_file, 'r') as f:
        content = f.read()

      # Extract docstring
      lines = content.split('\n')
      description = 'No description available'

      for i, line in enumerate(lines):
        if line.strip().startswith('"""') and i < 10:  # Look in first 10 lines
          if line.strip().count('"""') == 2:
            # Single line docstring
            description = line.strip()[3:-3].strip()
          else:
            # Multi-line docstring
            for j in range(i + 1, min(i + 5, len(lines))):
              if lines[j].strip() and not lines[j].strip().startswith('"""'):
                description = lines[j].strip()
                break
          break

      # Categorize based on tool name patterns
      name = tool_file.stem
      if any(x in name for x in ['get_current_user', 'get_workspace_info']):
        category = 'user'
      elif any(x in name for x in ['search_traces', 'get_trace', 'link_traces']):
        category = 'traces'
      elif any(x in name for x in ['review_app', 'get_review_app']):
        category = 'review-apps'
      elif any(x in name for x in ['labeling_session', 'labeling_schemas']):
        category = 'labeling'
      elif any(
        x in name for x in ['ai_analyze', 'analyze_labeling_results', 'analyze_trace_patterns']
      ):
        category = 'analytics'
      elif any(x in name for x in ['log_expectation', 'log_feedback']):
        category = 'logging'
      elif any(
        x in name
        for x in ['experiment', 'grant_experiment_permissions', 'update_config_experiment']
      ):
        category = 'mlflow'
      elif any(x in name for x in ['query_model_endpoint', 'list_model_endpoints']):
        category = 'endpoints'
      else:
        category = 'other'

      return description, category

    except Exception:
      return 'No description available', 'other'

  def list_tools(self, category: Optional[str] = None) -> None:
    """List all available tools, optionally filtered by category."""
    if not self.tools:
      print('No tools found in tools/ directory')
      return

    # Group tools by category
    categories = {}
    for tool in self.tools.values():
      if category and tool.category != category:
        continue
      if tool.category not in categories:
        categories[tool.category] = []
      categories[tool.category].append(tool)

    # Sort categories and tools
    for cat in sorted(categories.keys()):
      print(f'\n📁 {cat.upper()}')
      print('=' * (len(cat) + 4))

      for tool in sorted(categories[cat], key=lambda t: t.name):
        print(f'  {tool.name:<30} {tool.description}')

  def show_tool_help(self, tool_name: str) -> None:
    """Show detailed help for a specific tool."""
    if tool_name not in self.tools:
      print(f"❌ Tool '{tool_name}' not found")
      self._suggest_similar_tools(tool_name)
      return

    tool = self.tools[tool_name]
    print(f'🔧 {tool.name}')
    print('=' * (len(tool.name) + 4))
    print(f'Description: {tool.description}')
    print(f'Category: {tool.category}')
    print(f'Path: {tool.path}')
    print()

    # Try to run the tool with --help
    try:
      import subprocess

      result = subprocess.run(
        [sys.executable, str(tool.path), '--help'], capture_output=True, text=True, timeout=10
      )
      if result.returncode == 0:
        print('Usage:')
        print(result.stdout)
      else:
        print('Could not retrieve detailed help for this tool.')
    except Exception:
      print('Could not retrieve detailed help for this tool.')

  def run_tool(self, tool_name: str, args: List[str]) -> None:
    """Run a specific tool with the given arguments."""
    if tool_name not in self.tools:
      print(f"❌ Tool '{tool_name}' not found")
      self._suggest_similar_tools(tool_name)
      return

    tool = self.tools[tool_name]

    try:
      # Execute the tool by importing and running its main function
      spec = importlib.util.spec_from_file_location(tool_name, tool.path)
      if spec is None or spec.loader is None:
        raise ImportError(f'Could not load tool {tool_name}')

      module = importlib.util.module_from_spec(spec)

      # Set up sys.argv for the tool
      original_argv = sys.argv
      sys.argv = [str(tool.path)] + args

      try:
        spec.loader.exec_module(module)
        if hasattr(module, 'main'):
          main_func = module.main
          # Check if main is an async function
          if inspect.iscoroutinefunction(main_func):
            asyncio.run(main_func())
          else:
            main_func()
        else:
          print(f"❌ Tool '{tool_name}' does not have a main() function")
      finally:
        sys.argv = original_argv

    except SystemExit as e:
      # Tools may call sys.exit() - pass through the exit code
      sys.exit(e.code)
    except Exception as e:
      print(f"❌ Error running tool '{tool_name}': {str(e)}")
      sys.exit(1)

  def _suggest_similar_tools(self, tool_name: str) -> None:
    """Suggest similar tool names based on fuzzy matching."""
    suggestions = []
    for name in self.tools.keys():
      if tool_name in name or name in tool_name:
        suggestions.append(name)

    if suggestions:
      print('Did you mean one of these?')
      for suggestion in suggestions[:3]:  # Show top 3 suggestions
        print(f'  - {suggestion}')
    else:
      print("Use 'cli.py list' to see all available tools")

  def show_categories(self) -> None:
    """Show all available tool categories."""
    categories = set(tool.category for tool in self.tools.values())

    print('Available categories:')
    for category in sorted(categories):
      count = sum(1 for tool in self.tools.values() if tool.category == category)
      print(f'  {category:<15} ({count} tools)')

  def search_tools(self, query: str) -> None:
    """Search for tools by name or description."""
    query = query.lower()
    matches = []

    for tool in self.tools.values():
      if query in tool.name.lower() or query in tool.description.lower():
        matches.append(tool)

    if not matches:
      print(f"No tools found matching '{query}'")
      return

    print(f"Tools matching '{query}':")
    for tool in sorted(matches, key=lambda t: t.name):
      print(f'  {tool.name:<30} {tool.description}')


def main():
  """Main CLI entry point."""
  cli = UnifiedCLI()

  parser = argparse.ArgumentParser(
    description='Unified CLI for MLflow Review App operations',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=f"""
Available commands:
  list [category]           List all tools or tools in a specific category
  categories               Show all available categories
  search <query>           Search tools by name or description
  help <tool>              Show detailed help for a specific tool
  run <tool> [args...]     Run a specific tool with arguments

Quick examples:
  cli.py list                          # List all tools
  cli.py list traces                   # List trace-related tools
  cli.py search user                   # Search for user-related tools
  cli.py help search_traces            # Show help for search_traces tool
  cli.py run search_traces --limit 5   # Run search_traces with arguments

Total tools available: {len(cli.tools)}
        """,
  )

  parser.add_argument(
    'command',
    nargs='?',
    choices=['list', 'categories', 'search', 'help', 'run'],
    default='list',
    help='Command to execute',
  )

  parser.add_argument('args', nargs='*', help='Arguments for the command')

  args = parser.parse_args()

  if args.command == 'list':
    category = args.args[0] if args.args else None
    cli.list_tools(category)

  elif args.command == 'categories':
    cli.show_categories()

  elif args.command == 'search':
    if not args.args:
      print('❌ Search requires a query string')
      sys.exit(1)
    cli.search_tools(args.args[0])

  elif args.command == 'help':
    if not args.args:
      print('❌ Help requires a tool name')
      sys.exit(1)
    cli.show_tool_help(args.args[0])

  elif args.command == 'run':
    if not args.args:
      print('❌ Run requires a tool name')
      sys.exit(1)
    tool_name = args.args[0]
    tool_args = args.args[1:]
    cli.run_tool(tool_name, tool_args)


if __name__ == '__main__':
  main()
