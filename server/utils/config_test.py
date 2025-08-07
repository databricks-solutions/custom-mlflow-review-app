"""Tests for configuration management.

This module tests the application configuration loading and validation,
including the AppConfig singleton and environment variable handling.
"""

import os
from unittest.mock import MagicMock, patch

from server.utils.config import AppConfig


class TestAppConfig:
  """Test the AppConfig singleton class."""

  def setup_method(self):
    """Reset singleton state before each test."""
    if hasattr(AppConfig, '_instance'):
      AppConfig._instance = None
    if hasattr(AppConfig, '_config'):
      AppConfig._config = None

  def test_singleton_behavior(self):
    """Test that AppConfig is a singleton."""
    config1 = AppConfig()
    config2 = AppConfig()

    assert config1 is config2

  def test_config_properties_with_env_vars(self):
    """Test configuration property accessors with environment variables."""
    with patch.dict(
      os.environ,
      {
        'MLFLOW_EXPERIMENT_ID': '67890',
        'DEBUG': 'true',
        'DEVELOPERS': 'user1@example.com,user2@example.com',
        'SME_THANK_YOU_MESSAGE': 'Custom thank you message',
      },
    ):
      config = AppConfig()

      assert config.experiment_id == '67890'
      assert config.debug is True
      assert config.developers == ['user1@example.com', 'user2@example.com']
      assert config.sme_thank_you_message == 'Custom thank you message'
      assert config.max_results == 1000  # Default value
      assert config.page_size == 500  # Default value

  def test_config_defaults(self):
    """Test default values for configuration properties."""
    # Clear environment, mock load_dotenv, and reset singleton
    with (
      patch.dict(os.environ, {}, clear=True),
      patch('server.utils.config.load_dotenv', MagicMock()),
    ):
      AppConfig._instance = None  # Reset singleton
      AppConfig._config = None  # Reset config cache
      config = AppConfig()

      assert config.experiment_id == ''  # Empty default
      assert config.max_results == 1000  # Default value
      assert config.page_size == 500  # Default value
      assert config.debug is False  # Default value
      assert config.developers == []  # Empty default
      assert 'Thank you for participating' in config.sme_thank_you_message  # Default message

  def test_debug_boolean_parsing(self):
    """Test various boolean values for DEBUG environment variable."""
    test_cases = [
      ('true', True),
      ('True', True),
      ('1', True),
      ('yes', True),
      ('on', True),
      ('false', False),
      ('False', False),
      ('0', False),
      ('no', False),
      ('off', False),
      ('', False),
    ]

    for env_value, expected in test_cases:
      with patch.dict(os.environ, {'DEBUG': env_value}):
        config = AppConfig()
        assert config.debug == expected, f"DEBUG='{env_value}' should return {expected}"

  def test_developers_list_parsing(self):
    """Test developers list parsing from comma-separated values."""
    test_cases = [
      ('user1@example.com', ['user1@example.com']),
      ('user1@example.com,user2@example.com', ['user1@example.com', 'user2@example.com']),
      ('user1@example.com, user2@example.com ', ['user1@example.com', 'user2@example.com']),
      ('', []),
      ('user1@example.com,,user2@example.com', ['user1@example.com', 'user2@example.com']),
    ]

    for env_value, expected in test_cases:
      with patch.dict(os.environ, {'DEVELOPERS': env_value}):
        config = AppConfig()
        assert config.developers == expected, f"DEVELOPERS='{env_value}' should return {expected}"

  def test_get_method_backwards_compatibility(self):
    """Test the get() method for backwards compatibility."""
    with patch.dict(
      os.environ,
      {
        'MLFLOW_EXPERIMENT_ID': '12345',
        'DEVELOPERS': 'dev@example.com',
        'DEBUG': 'true',
      },
    ):
      config = AppConfig()

      # Test mapped keys
      assert config.get('mlflow.experiment_id') == '12345'
      assert config.get('experiment_id') == '12345'  # Test direct access
      assert config.get('developers') == ['dev@example.com']
      assert config.get('debug') is True

      # Test default values
      assert config.get('nonexistent') is None
      assert config.get('nonexistent', 'default') == 'default'
