"""Configuration loader for MLflow Review App."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv


class AppConfig:
  """Singleton configuration loader for the MLflow Review App."""

  _instance: Optional['AppConfig'] = None
  _config: Optional[Dict[str, Any]] = None

  def __new__(cls) -> 'AppConfig':
    """Create singleton instance of AppConfig."""
    if cls._instance is None:
      cls._instance = super().__new__(cls)
    return cls._instance

  def __init__(self):
    if self._config is None:
      self._load_config()

  def _load_config(self) -> None:
    """Load configuration from environment variables."""
    # Find the project root and load .env files
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent

    # Load .env and .env.local files
    env_files = [project_root / '.env', project_root / '.env.local']
    for env_file in env_files:
      if env_file.exists():
        load_dotenv(env_file)

    # Configuration is now loaded from environment variables
    self._config = {}

  def get(self, key_path: str, default: Any = None) -> Any:
    """Get configuration value using dot notation (e.g., 'mlflow.experiment_id').

    This method is kept for backward compatibility but now maps to environment variables.
    """
    # Map old key paths to environment variable names
    env_var_map = {
      'mlflow.experiment_id': 'MLFLOW_EXPERIMENT_ID',
      'experiment_id': 'MLFLOW_EXPERIMENT_ID',  # Direct access to experiment_id
      'model_endpoint': 'MODEL_ENDPOINT',
      'default_model_endpoint': 'MODEL_ENDPOINT',
      'developers': 'DEVELOPERS',
      'sme_thank_you_message': 'SME_THANK_YOU_MESSAGE',
      'debug': 'DEBUG',
    }

    env_var = env_var_map.get(key_path)
    if env_var:
      value = os.getenv(env_var)
      if value is not None:
        # Special handling for developers list (comma-separated)
        if key_path == 'developers':
          return [dev.strip() for dev in value.split(',') if dev.strip()] if value else []
        # Special handling for boolean values
        if key_path == 'debug':
          return value.lower() in ('true', '1', 'yes', 'on')
        return value

    return default

  # Convenience properties for commonly used config values
  @property
  def experiment_id(self) -> str:
    """Get the primary experiment ID."""
    return os.getenv('MLFLOW_EXPERIMENT_ID', '')

  @property
  def max_results(self) -> int:
    """Get the default max results for searches."""
    return 1000

  @property
  def page_size(self) -> int:
    """Get the default page size for paginated results."""
    return 500

  @property
  def debug(self) -> bool:
    """Get debug mode setting."""
    value = os.getenv('DEBUG', 'false').lower()
    return value in ('true', '1', 'yes', 'on')

  @property
  def sme_thank_you_message(self) -> str:
    """Get the SME thank you message."""
    return os.getenv(
      'SME_THANK_YOU_MESSAGE',
      'Thank you for participating to improve the quality of this Agent.',
    )

  @property
  def developers(self) -> List[str]:
    """Get the list of developer email addresses."""
    developers_str = os.getenv('DEVELOPERS', '')
    return (
      [dev.strip() for dev in developers_str.split(',') if dev.strip()] if developers_str else []
    )

  @property
  def model_endpoint(self) -> str:
    """Get the default model endpoint for AI analysis."""
    return os.getenv('MODEL_ENDPOINT', 'databricks-claude-sonnet-4')

  def reload(self) -> None:
    """Reload configuration from environment files."""
    self._config = None
    self._load_config()


# Global config instance
config = AppConfig()


def get_config() -> AppConfig:
  """Get the global configuration instance."""
  return config
