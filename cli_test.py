"""Tests for the unified CLI tool.

This module tests the unified CLI functionality including tool discovery,
command execution, and integration with individual tools.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cli import ToolInfo, UnifiedCLI


class TestUnifiedCLI:
  """Test the UnifiedCLI class."""

  def setup_method(self):
    """Set up test fixtures."""
    self.cli = UnifiedCLI()

  def test_tool_discovery(self):
    """Test that tools are discovered correctly."""
    # Should find tools in the tools directory
    assert len(self.cli.tools) > 0

    # Check that some expected tools are present
    expected_tools = ['get_current_user', 'search_traces', 'get_trace']
    for tool_name in expected_tools:
      assert tool_name in self.cli.tools

  def test_tool_info_structure(self):
    """Test that ToolInfo objects are created correctly."""
    if not self.cli.tools:
      pytest.skip('No tools found')

    tool = next(iter(self.cli.tools.values()))
    assert isinstance(tool, ToolInfo)
    assert tool.name
    assert tool.path.exists()
    assert tool.description
    assert tool.category

  def test_categorization(self):
    """Test that tools are categorized correctly."""
    if 'get_current_user' in self.cli.tools:
      assert self.cli.tools['get_current_user'].category == 'user'

    if 'search_traces' in self.cli.tools:
      assert self.cli.tools['search_traces'].category == 'traces'

  def test_list_tools_all(self):
    """Test listing all tools."""
    # Should not raise an exception
    self.cli.list_tools()

  def test_list_tools_by_category(self):
    """Test listing tools by category."""
    if not self.cli.tools:
      pytest.skip('No tools found')

    # Get a category that exists
    category = next(iter(self.cli.tools.values())).category
    self.cli.list_tools(category)

  def test_show_categories(self):
    """Test showing all categories."""
    self.cli.show_categories()

  def test_search_tools(self):
    """Test searching for tools."""
    if not self.cli.tools:
      pytest.skip('No tools found')

    # Search for something that should exist
    self.cli.search_tools('user')
    self.cli.search_tools('trace')
    self.cli.search_tools('nonexistent')

  def test_show_tool_help_existing(self):
    """Test showing help for an existing tool."""
    if 'get_current_user' in self.cli.tools:
      # Should not raise an exception
      self.cli.show_tool_help('get_current_user')

  def test_show_tool_help_nonexistent(self):
    """Test showing help for a non-existent tool."""
    # Should not raise an exception, just print error
    self.cli.show_tool_help('nonexistent_tool')

  def test_suggest_similar_tools(self):
    """Test similar tool suggestions."""
    if 'get_current_user' in self.cli.tools:
      # Should suggest similar tools for partial matches
      self.cli._suggest_similar_tools('current')


class TestToolInfo:
  """Test the ToolInfo class."""

  def test_tool_info_creation(self):
    """Test ToolInfo object creation."""
    path = Path(__file__)
    tool = ToolInfo(name='test_tool', path=path, description='Test description', category='test')

    assert tool.name == 'test_tool'
    assert tool.path == path
    assert tool.description == 'Test description'
    assert tool.category == 'test'


class TestCLIIntegration:
  """Test CLI integration with actual tools."""

  def setup_method(self):
    """Set up test fixtures."""
    self.cli = UnifiedCLI()

  @patch('subprocess.run')
  def test_show_tool_help_with_subprocess(self, mock_run):
    """Test showing tool help using subprocess."""
    if 'get_current_user' not in self.cli.tools:
      pytest.skip('get_current_user tool not found')

    # Mock successful subprocess run
    mock_run.return_value = MagicMock(returncode=0, stdout='Mock help output')

    self.cli.show_tool_help('get_current_user')
    mock_run.assert_called_once()

  def test_extract_tool_info(self):
    """Test extracting tool information from files."""
    if not self.cli.tools:
      pytest.skip('No tools found')

    # Test with an actual tool file
    tool_file = next(iter(self.cli.tools.values())).path
    description, category = self.cli._extract_tool_info(tool_file)

    assert isinstance(description, str)
    assert isinstance(category, str)
    assert description != ''
    assert category != ''


class TestCLIErrorHandling:
  """Test CLI error handling."""

  def setup_method(self):
    """Set up test fixtures."""
    self.cli = UnifiedCLI()

  def test_nonexistent_tool_execution(self):
    """Test running a non-existent tool."""
    # Should handle gracefully without raising exception
    self.cli.run_tool('nonexistent_tool', [])

  def test_empty_tools_directory(self):
    """Test behavior with empty tools directory."""
    # Create CLI with mock empty tools
    cli = UnifiedCLI()
    cli.tools = {}

    # Should handle gracefully
    cli.list_tools()
    cli.show_categories()
    cli.search_tools('test')
