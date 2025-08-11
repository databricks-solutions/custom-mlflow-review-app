#!/usr/bin/env python3
"""Databricks App Setup Script
Interactive setup for Databricks Apps with authentication, experiment configuration, and OBO setup.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# Import functions from existing modules
from app_status import (
  check_user_authorization_sp_permissions,
  get_app_status,
  get_experiment_permissions,
  get_workspace_obo_status,
  load_env_local,
)
from check_permissions import check_permissions, fix_permissions, format_text_output

try:
  from rich.console import Console
  from rich.panel import Panel
  from rich.progress import Progress, SpinnerColumn, TextColumn
  from rich.prompt import Confirm, Prompt
  from rich.table import Table
  from rich.text import Text

  RICH_AVAILABLE = True
except ImportError:
  RICH_AVAILABLE = False

  # Fallback to basic print statements
  class Console:
    def print(self, *args, **kwargs):
      print(*args)

  class Prompt:
    @staticmethod
    def ask(prompt: str, default: str = None) -> str:
      if default:
        response = input(f'{prompt} [{default}]: ')
        return response if response else default
      return input(f'{prompt}: ')

  class Confirm:
    @staticmethod
    def ask(prompt: str) -> bool:
      response = input(f'{prompt} (y/N): ').lower()
      return response in ['y', 'yes']


console = Console()


class SetupError(Exception):
  """Custom exception for setup errors."""

  pass


class DatabricksAppSetup:
  """Main setup class for Databricks App configuration."""

  def __init__(self, auto_close: bool = False, temp_file: Optional[str] = None):
    self.auto_close = auto_close
    self.temp_file = temp_file
    self.env_file = Path('.env.local')
    self.config_file = Path('config.yaml')

    # State variables
    self.env_vars: Dict[str, str] = {}
    self.auth_type: Optional[str] = None
    self.profile: Optional[str] = None
    self.workspace_host: Optional[str] = None
    self.experiment_id: Optional[str] = None
    self.experiment_name: Optional[str] = None
    self.app_name: Optional[str] = None
    self.workspace_obo_enabled: Optional[bool] = None

  def cleanup(self):
    """Signal completion on exit."""
    if self.auto_close and self.temp_file:
      try:
        with open(self.temp_file, 'w') as f:
          f.write('setup_complete')
      except Exception:
        pass

  def run_command(self, cmd: List[str], timeout: int = 30) -> Tuple[bool, str]:
    """Run a shell command and return success status and output."""
    try:
      result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
      return result.returncode == 0, result.stdout if result.returncode == 0 else result.stderr
    except subprocess.TimeoutExpired:
      return False, 'Command timed out'
    except Exception as e:
      return False, f'Command failed: {e}'

  def check_tool_installed(self, tool: str) -> bool:
    """Check if a tool is installed and available."""
    return shutil.which(tool) is not None

  def install_tools(self):
    """Install required tools: databricks, uv, bun."""
    console.print('\n🔧 Checking dependencies...\n')

    tools_to_install = []

    # Check databricks CLI
    if not self.check_tool_installed('databricks'):
      tools_to_install.append('databricks')

    # Check uv
    if not self.check_tool_installed('uv'):
      tools_to_install.append('uv')

    # Check bun
    if not self.check_tool_installed('bun'):
      tools_to_install.append('bun')

    if not tools_to_install:
      console.print('✅ All required tools are available')
      return

    console.print(f'Installing missing tools: {", ".join(tools_to_install)}')

    # Install databricks CLI
    if 'databricks' in tools_to_install:
      console.print('📦 Installing Databricks CLI...')
      if shutil.which('brew'):
        success1, _ = self.run_command(['brew', 'tap', 'databricks/tap'])
        success2, output = self.run_command(['brew', 'install', 'databricks'])
        if not (success1 and success2):
          console.print('❌ Failed to install Databricks CLI via brew')
          console.print(
            'Please install manually: https://docs.databricks.com/dev-tools/cli/install.html'
          )
          raise SetupError('Databricks CLI installation failed')
      else:
        console.print('❌ Databricks CLI not found and brew not available')
        console.print('Please install Databricks CLI manually:')
        console.print('   Visit: https://docs.databricks.com/dev-tools/cli/install.html')
        raise SetupError('Databricks CLI installation required')

    # Install uv
    if 'uv' in tools_to_install:
      console.print('📦 Installing uv...')
      success, output = self.run_command(['curl', '-LsSf', 'https://astral.sh/uv/install.sh'])
      if success:
        # Run the install script
        success, _ = self.run_command(['sh'], timeout=120)  # Give more time for install
        if success:
          # Update PATH
          uv_paths = [os.path.expanduser('~/.local/bin'), os.path.expanduser('~/.cargo/bin')]
          for path in uv_paths:
            if path not in os.environ.get('PATH', ''):
              os.environ['PATH'] = f'{path}:{os.environ.get("PATH", "")}'
        else:
          console.print('❌ Failed to install uv')
          raise SetupError('uv installation failed')
      else:
        console.print('❌ Failed to download uv installer')
        raise SetupError('uv download failed')

    # Install bun
    if 'bun' in tools_to_install:
      console.print('📦 Installing bun...')
      success, output = self.run_command(['curl', '-fsSL', 'https://bun.sh/install'])
      if success:
        # Run the install script
        success, _ = self.run_command(['bash'], timeout=120)
        if success:
          # Update PATH
          bun_path = os.path.expanduser('~/.bun/bin')
          if bun_path not in os.environ.get('PATH', ''):
            os.environ['PATH'] = f'{bun_path}:{os.environ.get("PATH", "")}'
        else:
          console.print('❌ Failed to install bun')
          raise SetupError('bun installation failed')
      else:
        console.print('❌ Failed to download bun installer')
        raise SetupError('bun download failed')

    console.print('✅ All required tools are now available\n')

  def load_existing_config(self):
    """Load existing configuration from .env.local."""
    if self.env_file.exists():
      self.env_vars = load_env_local()
      console.print('📋 Found existing .env.local file.')

      if Confirm.ask('Keep existing configuration?', default=True):
        console.print('✅ Using existing configuration.')
        return False
      else:
        console.print('📝 Updating configuration...')

    return True

  def update_env_value(self, key: str, value: str, comment: str = None):
    """Update or add a value in .env.local."""
    lines = []
    key_updated = False

    # Read existing lines
    if self.env_file.exists():
      with open(self.env_file, 'r') as f:
        lines = f.readlines()

    # Update existing key or mark for addition
    for i, line in enumerate(lines):
      if line.strip().startswith(f'{key}='):
        lines[i] = f'{key}={value}\n'
        key_updated = True
        break

    # Add new key if not found
    if not key_updated:
      if comment:
        lines.extend(['\n', f'# {comment}\n'])
      lines.append(f'{key}={value}\n')

    # Write back to file
    with open(self.env_file, 'w') as f:
      f.writelines(lines)

    # Update internal state
    self.env_vars[key] = value
    os.environ[key] = value

  def initialize_env_file(self):
    """Initialize .env.local with header."""
    if not self.env_file.exists():
      with open(self.env_file, 'w') as f:
        f.write('# Databricks App Configuration\n')
        f.write(f'# Generated by setup script on {os.popen("date").read().strip()}\n')
        f.write('\n')

  def test_databricks_connection(self, profile: Optional[str] = None) -> bool:
    """Test Databricks connection."""
    console.print('🔍 Testing Databricks connection...')

    # Ensure environment variables are exported
    if self.env_vars.get('DATABRICKS_HOST') and self.env_vars.get('DATABRICKS_TOKEN'):
      os.environ['DATABRICKS_HOST'] = self.env_vars['DATABRICKS_HOST']
      os.environ['DATABRICKS_TOKEN'] = self.env_vars['DATABRICKS_TOKEN']

    cmd = ['databricks', 'current-user', 'me']
    if profile:
      cmd.extend(['--profile', profile])

    success, output = self.run_command(cmd)

    if success:
      console.print(
        f'✅ Successfully connected to Databricks{f" with profile {profile}" if profile else ""}'
      )
      return True
    else:
      console.print(
        f'❌ Failed to connect to Databricks{f" with profile {profile}" if profile else ""}'
      )
      console.print(f'Error: {output}')
      return False

  def setup_authentication(self) -> bool:
    """Set up Databricks authentication."""
    console.print('\n🔐 Databricks Authentication')
    console.print('-' * 30)

    self.initialize_env_file()

    console.print('Choose authentication method:')
    console.print('1. Personal Access Token (PAT)')
    console.print('2. Configuration Profile')
    console.print('')

    # Pre-select based on existing configuration
    current_auth = self.env_vars.get('DATABRICKS_AUTH_TYPE')
    if current_auth == 'pat':
      default_choice = '1'
    elif current_auth == 'profile':
      default_choice = '2'
    else:
      default_choice = None

    auth_choice = Prompt.ask('Select option', choices=['1', '2'], default=default_choice)

    if auth_choice == '1':
      return self.setup_pat_auth()
    else:
      return self.setup_profile_auth()

  def setup_pat_auth(self) -> bool:
    """Set up Personal Access Token authentication."""
    console.print('\n📝 Personal Access Token Setup')
    console.print('-' * 31)

    self.update_env_value('DATABRICKS_AUTH_TYPE', 'pat', 'Databricks Authentication Type')

    # Get host
    current_host = self.env_vars.get('DATABRICKS_HOST', '')
    if current_host:
      console.print(f'Current Databricks Host: {current_host}')
      if Confirm.ask('Keep this host?', default=True):
        host = current_host
      else:
        host = Prompt.ask('Databricks Host', default=current_host)
    else:
      # No existing host found in .env.local
      host = Prompt.ask('Databricks Host (e.g., https://your-workspace.cloud.databricks.com)')

    self.update_env_value('DATABRICKS_HOST', host, 'Databricks Configuration (PAT mode)')
    self.workspace_host = host

    # Get token
    current_token = self.env_vars.get('DATABRICKS_TOKEN', '')
    if current_token:
      console.print(f'Found existing token: {current_token[:10]}... (truncated)')
      if Confirm.ask('Use this existing token?', default=True):
        token = current_token
      else:
        token = ''
    else:
      token = ''

    if not token:
      console.print('\nYou can create a Personal Access Token here:')
      console.print(f'📖 {host}/settings/user/developer/access-tokens')
      console.print('')
      token = Prompt.ask('Databricks Personal Access Token', password=True)

    self.update_env_value('DATABRICKS_TOKEN', token)

    # Clear profile settings
    self.update_env_value('DATABRICKS_CONFIG_PROFILE', '')
    self.auth_type = 'pat'

    return self.test_databricks_connection()

  def setup_profile_auth(self) -> bool:
    """Set up profile-based authentication."""
    console.print('\n📋 Configuration Profile Setup')
    console.print('-' * 32)

    self.update_env_value('DATABRICKS_AUTH_TYPE', 'profile', 'Databricks Authentication Type')

    # List existing profiles
    console.print('Available profiles:')
    config_file = Path.home() / '.databrickscfg'
    if config_file.exists():
      with open(config_file, 'r') as f:
        profiles = [line.strip().strip('[]') for line in f if line.strip().startswith('[')]
        for profile in profiles:
          console.print(f'  - {profile}')
    else:
      console.print('  No existing profiles found')
    console.print('')

    current_profile = self.env_vars.get('DATABRICKS_CONFIG_PROFILE', 'DEFAULT')
    profile = Prompt.ask('Databricks Config Profile', default=current_profile)

    self.update_env_value(
      'DATABRICKS_CONFIG_PROFILE', profile, 'Databricks Configuration (Profile mode)'
    )

    # Clear PAT credentials
    self.update_env_value('DATABRICKS_HOST', '')
    self.update_env_value('DATABRICKS_TOKEN', '')
    self.auth_type = 'profile'
    self.profile = profile

    # Test profile
    if not self.test_databricks_connection(profile):
      console.print(f"\nProfile '{profile}' not found or invalid.")
      if Confirm.ask('Configure this profile now?', default=True):
        success, output = self.run_command(['databricks', 'configure', '--profile', profile])
        if not success or not self.test_databricks_connection(profile):
          console.print('❌ Profile configuration failed. Please check your settings.')
          return False
      else:
        console.print('❌ Valid Databricks authentication is required.')
        return False

    return True

  def get_current_user_info(self) -> Optional[str]:
    """Get current user information."""
    console.print('\n🔍 Getting user information...')

    cmd = ['databricks', 'current-user', 'me', '--output', 'json']
    if self.auth_type == 'profile' and self.profile:
      cmd.extend(['--profile', self.profile])

    success, output = self.run_command(cmd)

    if success:
      try:
        user_data = json.loads(output)
        username = user_data.get('userName', '')
        if username:
          console.print(f'✅ Detected user: {username}')
          return username
      except json.JSONDecodeError:
        pass

    console.print('⚠️  Could not detect user, will use default paths')
    return None

  def setup_developer_access(self) -> bool:
    """Add current user to developers array in config.yaml."""
    console.print('\n👤 Setting up developer access...')

    # Get current user email
    current_user_email = self.get_current_user_email()
    if not current_user_email:
      console.print('⚠️  Could not determine current user email')
      return True  # Continue setup even if we can't add developer

    console.print(f'✅ Detected user: {current_user_email}')

    # Load or create config.yaml
    config = self.load_config_yaml()

    # Ensure developers array exists
    if 'developers' not in config:
      config['developers'] = []

    # Add current user if not already present
    if current_user_email not in config['developers']:
      config['developers'].append(current_user_email)
      console.print(f'📝 Added {current_user_email} to developers array')

      # Save the config
      self._save_config_env(config)
    else:
      console.print(f'✅ User {current_user_email} already in developers array')

    return True

  def _save_config_env(self, config: Dict[str, Any]):
    """Save configuration to .env file."""
    env_file = Path('.env')

    # Update MLflow experiment ID
    if 'mlflow' in config and 'experiment_id' in config['mlflow']:
      self.update_env_file_value(
        env_file, 'MLFLOW_EXPERIMENT_ID', config['mlflow']['experiment_id']
      )

    # Update developers (comma-separated)
    if 'developers' in config and config['developers']:
      developers_str = ','.join(config['developers'])
      self.update_env_file_value(env_file, 'DEVELOPERS', developers_str)

    # Update SME thank you message
    if 'sme_thank_you_message' in config:
      self.update_env_file_value(env_file, 'SME_THANK_YOU_MESSAGE', config['sme_thank_you_message'])

  def update_env_file_value(self, env_path: Path, key: str, value: str):
    """Update or add a value in a specific env file."""
    lines = []
    key_updated = False

    # Read existing lines
    if env_path.exists():
      with open(env_path, 'r') as f:
        lines = f.readlines()

    # Update existing key or mark for addition
    for i, line in enumerate(lines):
      if line.strip().startswith(f'{key}='):
        lines[i] = f'{key}={value}\n'
        key_updated = True
        break

    # Add new key if not found
    if not key_updated:
      lines.append(f'{key}={value}\n')

    # Write back to file
    with open(env_path, 'w') as f:
      f.writelines(lines)

  def get_current_user_email(self) -> Optional[str]:
    """Get current user email from Databricks CLI."""
    cmd = ['databricks', 'current-user', 'me', '--output', 'json']
    if self.auth_type == 'profile' and self.profile:
      cmd.extend(['--profile', self.profile])

    success, output = self.run_command(cmd)
    if success:
      try:
        user_data = json.loads(output)
        user_name = user_data.get('userName', '')
        emails = user_data.get('emails', [])

        # Prefer primary email, fallback to userName if it looks like email
        if emails and len(emails) > 0:
          for email_obj in emails:
            if isinstance(email_obj, dict):
              primary_email = email_obj.get('value') or email_obj.get('primary')
              if primary_email:
                return primary_email

        # If userName looks like email, use it
        if user_name and '@' in user_name:
          return user_name

      except json.JSONDecodeError:
        pass

    return None

  def setup_app_configuration(self, username: Optional[str]) -> bool:
    """Set up app configuration."""
    console.print('\n🚀 App Configuration')
    console.print('-' * 20)

    # Show app creation URL
    console.print(
      "If you haven't created a Databricks App yet, you can create a custom app from the UI:"
    )
    if self.workspace_host:
      console.print(f'📖 {self.workspace_host}/apps/create')
    else:
      console.print('📖 https://your-workspace.cloud.databricks.com/apps/create')
    console.print('')

    # Get app name
    current_app_name = self.env_vars.get('DATABRICKS_APP_NAME', '')
    if current_app_name:
      console.print(f'Current App Name: {current_app_name}')
      if Confirm.ask('Keep this app name?', default=True):
        self.app_name = current_app_name
      else:
        self.app_name = Prompt.ask('App Name for Deployment', default=current_app_name)
    else:
      self.app_name = Prompt.ask('App Name for Deployment', default='my-databricks-app')

    # Set source path
    current_source_path = self.env_vars.get('DBA_SOURCE_CODE_PATH', '')
    if current_source_path:
      console.print(f'Current Source Code Path: {current_source_path}')
      if Confirm.ask('Keep this source path?', default=True):
        source_path = current_source_path
      else:
        source_path = Prompt.ask('Source Code Path for Deployment', default=current_source_path)
    else:
      # Generate default path
      if username:
        default_source_path = f'/Workspace/Users/{username}/{self.app_name}'
      else:
        default_source_path = f'/Workspace/Users/<your-email@company.com>/{self.app_name}'
      source_path = Prompt.ask('Source Code Path for Deployment', default=default_source_path)

    # Update configuration
    self.update_env_value('DATABRICKS_APP_NAME', self.app_name, 'Databricks App Configuration')
    self.update_env_value('DBA_SOURCE_CODE_PATH', source_path)

    console.print('\n✅ Environment configuration saved to .env.local')
    return True

  def load_config_yaml(self) -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    if not self.config_file.exists():
      return {}

    try:
      with open(self.config_file, 'r') as f:
        return yaml.safe_load(f) or {}
    except Exception as e:
      console.print(f'⚠️  Failed to load config.yaml: {e}')
      return {}

  def validate_experiment(self, experiment_input: str) -> Tuple[Optional[str], Optional[str]]:
    """Validate experiment and return (experiment_id, experiment_name)."""
    # Try by ID first if input is numeric
    if experiment_input.isdigit():
      console.print('🔢 Input appears to be an experiment ID, validating...')
      cmd = [
        'databricks',
        'api',
        'get',
        f'/api/2.0/mlflow/experiments/get?experiment_id={experiment_input}',
      ]
      if self.auth_type == 'profile' and self.profile:
        cmd.extend(['--profile', self.profile])

      success, output = self.run_command(cmd)
      if success:
        try:
          data = json.loads(output)
          experiment = data.get('experiment', {})
          name = experiment.get('name', 'Unknown')
          return experiment_input, name
        except json.JSONDecodeError:
          pass

    # Try to search by name
    console.print(f'📝 Searching for experiment by name: {experiment_input}')
    cmd = ['databricks', 'api', 'get', '/api/2.0/mlflow/experiments/search']
    if self.auth_type == 'profile' and self.profile:
      cmd.extend(['--profile', self.profile])

    success, output = self.run_command(cmd)
    if success:
      try:
        data = json.loads(output)
        experiments = data.get('experiments', [])

        # Look for exact match first
        for exp in experiments:
          if exp.get('name', '').lower() == experiment_input.lower():
            return exp.get('experiment_id', ''), exp.get('name', '')

        # Look for partial matches
        matches = []
        for exp in experiments:
          if experiment_input.lower() in exp.get('name', '').lower():
            matches.append((exp.get('experiment_id', ''), exp.get('name', '')))

        if matches:
          console.print('❌ No exact match found. Did you mean one of these?')
          for i, (exp_id, name) in enumerate(matches[:5]):
            console.print(f'   {i + 1}. {name} (ID: {exp_id})')
          return None, None

      except json.JSONDecodeError:
        pass

    console.print(f'❌ Could not find experiment: {experiment_input}')
    return None, None

  def setup_mlflow_experiment(self) -> bool:
    """Set up MLflow experiment configuration."""
    console.print('\n🧪 MLflow Experiment Configuration')
    console.print('-' * 34)
    console.print('The Review App needs an MLflow experiment to analyze traces from.')
    console.print('You can provide either an experiment name or experiment ID.\n')

    # Load existing experiment ID
    config = self.load_config_yaml()
    current_experiment_id = config.get('mlflow', {}).get('experiment_id', '')

    if current_experiment_id:
      console.print(f'✅ Found existing experiment in config.yaml: {current_experiment_id}')
      if Confirm.ask('Use this existing experiment?', default=True):
        console.print('✅ Keeping existing experiment configuration.')
        self.experiment_id = current_experiment_id
        # Need to get experiment name for display
        exp_id, exp_name = self.validate_experiment(current_experiment_id)
        if exp_name:
          self.experiment_name = exp_name
        else:
          self.experiment_name = f'Experiment {current_experiment_id}'
        # Continue to permissions management instead of returning early
      else:
        console.print('📝 Configuring different experiment...')
        # Flag to indicate we need to get a new experiment
        current_experiment_id = None

    # Get experiment from user only if we don't have one yet
    if not self.experiment_id:
      while True:
        experiment_input = Prompt.ask('Enter MLflow experiment name or ID')

        if not experiment_input.strip():
          console.print('❌ Experiment name or ID cannot be empty')
          continue

        console.print(f'🔍 Validating experiment: {experiment_input}')
        exp_id, exp_name = self.validate_experiment(experiment_input)

        if exp_id:
          console.print('✅ Found experiment:')
          console.print(f'   Name: {exp_name}')
          console.print(f'   ID: {exp_id}')

          if Confirm.ask('Use this experiment?', default=True):
            self.experiment_id = exp_id
            self.experiment_name = exp_name
            break
        else:
          console.print('\nPlease try again with a valid experiment name or ID.')

    # Show detailed experiment information and manage permissions
    if not self.show_experiment_info_and_manage_permissions():
      console.print('⚠️ Failed to manage experiment permissions, but continuing with setup...')

    # Update config.yaml
    self.update_config_yaml()
    console.print(
      f'✅ MLflow experiment configured: {self.experiment_name} (ID: {self.experiment_id})'
    )

    return True

  def update_config_yaml(self):
    """Update or create .env.local with experiment configuration."""
    console.print('📝 Updating .env.local...')

    config = self.load_config_yaml()

    # Ensure mlflow section exists
    if 'mlflow' not in config:
      config['mlflow'] = {}

    config['mlflow']['experiment_id'] = self.experiment_id

    # Set up developers array with current user
    if 'developers' not in config:
      config['developers'] = []

    # Add current user as developer if we can determine their email
    current_user_email = self.get_current_user_email()
    if current_user_email and current_user_email not in config['developers']:
      config['developers'].append(current_user_email)
      console.print(f'👤 Added {current_user_email} as developer')

    # Preserve or create SME message
    if 'sme_thank_you_message' not in config:
      config['sme_thank_you_message'] = (
        'Thank you for participating to improve the quality of this Agent. '
        "Your expertise has made a huge impact, and every interaction you've "
        'reviewed helps the chatbot become smarter and more user-friendly. '
        'Thank you for your dedication and valuable insights.'
      )

    # Save to .env.local file
    self._save_config_env(config)

  def show_experiment_info_and_manage_permissions(self) -> bool:
    """Display experiment information and manage developer permissions."""
    try:
      console.print('\n📊 EXPERIMENT INFORMATION')
      console.print('=' * 25)
      console.print(f'Name: {self.experiment_name}')
      console.print(f'ID: {self.experiment_id}')

      # Show experiment URL
      if self.workspace_host:
        experiment_url = f'{self.workspace_host}/ml/experiments/{self.experiment_id}/traces'
        console.print(f'🔗 URL: {experiment_url}')

      console.print('')

      # Use check_permissions to get comprehensive permission status
      console.print('🔍 Checking experiment permissions...')
      check_result = check_permissions(
        self.experiment_id,
        self.auth_type,
        self.profile if self.auth_type == 'profile' else None,
        self.app_name,
      )

      if check_result.get('error'):
        console.print(f'❌ Failed to check permissions: {check_result["error"]}')
        return False

      # Display formatted permission output as plain text to avoid rich auto-coloring
      output = format_text_output(check_result)
      # Print line by line without rich formatting
      for line in output.split('\n'):
        print(line)
      print('')

      # If there are missing permissions, offer to fix them
      if check_result['status'] == 'MISSING_PERMISSIONS':
        console.print('⚠️ Some principals are missing required permissions!')
        if Confirm.ask('\n🔧 Grant missing CAN_MANAGE permissions?', default=True):
          fix_result = fix_permissions(check_result, self.experiment_id, interactive=False)

          if fix_result.get('fixed'):
            console.print(
              f'\n✅ Successfully granted permissions to: {", ".join(fix_result["fixed"])}'
            )

            # Re-check permissions
            console.print('\n🔍 Re-verifying permissions...')
            updated_check = check_permissions(
              self.experiment_id,
              self.auth_type,
              self.profile if self.auth_type == 'profile' else None,
              self.app_name,
            )
            # Print without rich formatting
            output = format_text_output(updated_check)
            for line in output.split('\n'):
              print(line)

          if fix_result.get('failed'):
            console.print(f'\n❌ Failed to grant permissions to: {", ".join(fix_result["failed"])}')
            console.print('⚠️ You may need to grant these permissions manually')
      else:
        console.print('✅ All required permissions are already configured correctly!')

      # Ask for additional developers
      console.print('\n👥 ADDITIONAL DEVELOPER ACCESS')
      console.print('=' * 32)
      console.print('Add other developers who need CAN_MANAGE access to this experiment.')
      console.print(
        'This allows them to view traces, create labeling sessions, and manage the experiment.'
      )
      console.print('')

      developers_input = Prompt.ask(
        'Enter developer email addresses (comma-separated, or press Enter to skip)', default=''
      )

      if developers_input.strip():
        # Parse and clean the developer list
        new_developers = [email.strip() for email in developers_input.split(',') if email.strip()]

        # Get current managers from check_result
        current_managers = []
        for dev in check_result.get('summary', {}).get('developers', []):
          if dev.get('has_can_manage'):
            current_managers.append(dev['email'])

        # Filter out developers who already have CAN_MANAGE access
        developers_to_add = [dev for dev in new_developers if dev not in current_managers]

        if developers_to_add:
          console.print(
            f'\n🔧 Will grant CAN_MANAGE permissions to: {", ".join(developers_to_add)}'
          )
          if Confirm.ask('Proceed with granting permissions?', default=True):
            console.print('')
            success_count = 0
            for developer_email in developers_to_add:
              if self.grant_experiment_permission(developer_email):
                console.print(f'✅ Granted CAN_MANAGE permission to {developer_email}')
                success_count += 1
              else:
                console.print(f'❌ Failed to grant permission to {developer_email}')

            # Add all developers to config.yaml (including those who already had permissions)
            if success_count > 0 or new_developers:
              console.print('\n📝 Adding developer(s) to config.yaml...')
              self.add_developers_to_config(new_developers)
          else:
            console.print('❌ Permission granting cancelled')
        else:
          if new_developers:
            console.print('✅ All specified developers already have CAN_MANAGE access')
            # Still add them to config.yaml if not already there
            console.print('📝 Adding developers to config.yaml...')
            self.add_developers_to_config(new_developers)

      # Final verification
      if developers_input.strip() or check_result['status'] == 'MISSING_PERMISSIONS':
        console.print('\n🔍 VERIFYING FINAL PERMISSIONS')
        console.print('=' * 32)

        final_check = check_permissions(
          self.experiment_id,
          self.auth_type,
          self.profile if self.auth_type == 'profile' else None,
          self.app_name,
        )

        # Print without rich formatting to avoid auto-coloring
        output = format_text_output(final_check)
        for line in output.split('\n'):
          print(line)

        if final_check['status'] == 'OK':
          console.print('\n✅ All permissions successfully configured!')
        else:
          console.print('\n⚠️ Some permissions may still need manual configuration')

      return True

    except Exception as e:
      console.print(f'❌ Error managing experiment permissions: {e}')
      return False

  def grant_experiment_permission(self, user_email: str) -> bool:
    """Grant CAN_MANAGE permission to a user for the current experiment."""
    try:
      # Use the grant_experiment_permissions tool
      cmd = [
        'uv',
        'run',
        'python',
        'tools/grant_experiment_permissions.py',
        '--experiment-id',
        self.experiment_id,
        '--principal-type',
        'user',
        '--principal-id',
        user_email,
        '--permission',
        'CAN_MANAGE',
      ]

      success, output = self.run_command(cmd, timeout=60)
      return success

    except Exception as e:
      console.print(f'❌ Error granting permission: {e}')
      return False

  def add_developers_to_config(self, developer_emails: list) -> bool:
    """Add developers to the config.yaml developers array."""
    try:
      config = self.load_config_yaml()

      # Ensure developers array exists
      if 'developers' not in config:
        config['developers'] = []

      # Add new developers if not already present
      added_count = 0
      for dev_email in developer_emails:
        if dev_email not in config['developers']:
          config['developers'].append(dev_email)
          console.print(f'   ➕ Added {dev_email} to config.yaml')
          added_count += 1
        else:
          console.print(f'   ✅ {dev_email} already in config.yaml')

      if added_count > 0:
        # Save updated config
        self._save_config_env(config)
        console.print(f'📝 Updated config.yaml with {added_count} new developer(s)')

      return True

    except Exception as e:
      console.print(f'❌ Error updating config.yaml: {e}')
      return False

  def setup_model_endpoint(self) -> bool:
    """Set up model serving endpoint for AI analysis (optional)."""
    console.print('\n🤖 AI ANALYSIS MODEL ENDPOINT SETUP')
    console.print('=' * 40)
    console.print('')
    console.print('The Review App can use AI analysis to provide insights about:')
    console.print('• Experiment performance and patterns')
    console.print('• Labeling session quality and recommendations')
    console.print('• SME engagement analysis')
    console.print('')
    console.print('This feature is optional and requires a model serving endpoint.')
    console.print('')

    if not Confirm.ask('Would you like to configure AI analysis?', default=True):
      console.print('⏭️  Skipping AI analysis configuration.')
      return True

    console.print('')
    console.print('📋 Fetching available model serving endpoints...')

    try:
      # Use our list_model_endpoints tool to get available endpoints
      result = subprocess.run(
        ['uv', 'run', 'python', 'tools/list_model_endpoints.py', '--format', 'json'],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
      )

      if result.returncode != 0:
        console.print('⚠️  Could not fetch model endpoints. You can configure this manually later.')
        console.print(f'   Error: {result.stderr}')
        return True

      endpoints_data = json.loads(result.stdout)

      # Filter to only show READY endpoints
      ready_endpoints = [ep for ep in endpoints_data if ep.get('state') == 'READY']

      if not ready_endpoints:
        console.print('❌ No ready model serving endpoints found in your workspace.')
        console.print('   You can create endpoints in Databricks and configure this later.')
        return True

      console.print(f'✅ Found {len(ready_endpoints)} ready model serving endpoints')
      console.print('')

      # Show endpoint options
      console.print('Available endpoints:')

      # Group endpoints by type for better display
      databricks_endpoints = [ep for ep in ready_endpoints if ep['name'].startswith('databricks-')]
      user_endpoints = [ep for ep in ready_endpoints if not ep['name'].startswith('databricks-')]

      options = []

      if databricks_endpoints:
        console.print('\n🏢 Databricks Foundation Models:')
        for i, ep in enumerate(databricks_endpoints[:10]):  # Limit to top 10
          name = ep['name']
          creator = ep.get('creator', 'N/A')
          console.print(f'  {len(options)+1}. {name}')
          if creator != 'N/A':
            console.print(f'      Creator: {creator}')
          options.append(ep)

      if user_endpoints:
        console.print('\n👤 User/Custom Endpoints:')
        for i, ep in enumerate(user_endpoints[:10]):  # Limit to top 10
          name = ep['name']
          creator = ep.get('creator', 'N/A')
          console.print(f'  {len(options)+1}. {name}')
          if creator != 'N/A':
            console.print(f'      Creator: {creator}')
          options.append(ep)

      console.print('')
      console.print('💡 Recommended: databricks-claude-sonnet-4 (powerful, fast AI analysis)')
      console.print('')

      while True:
        try:
          choice = Prompt.ask(
            'Select an endpoint by number (or press Enter for databricks-claude-sonnet-4)',
            default='',
          )

          if not choice.strip():
            # Default to databricks-claude-sonnet-4
            selected_endpoint = 'databricks-claude-sonnet-4'
            break

          choice_num = int(choice) - 1
          if 0 <= choice_num < len(options):
            selected_endpoint = options[choice_num]['name']
            break
          else:
            console.print(f'❌ Please select a number between 1 and {len(options)}')

        except ValueError:
          console.print('❌ Please enter a valid number')

      # Update .env file with selected endpoint
      env_file = Path('.env')
      if env_file.exists():
        # Read current .env content
        with open(env_file, 'r') as f:
          lines = f.readlines()

        # Update or add MODEL_ENDPOINT
        updated = False
        for i, line in enumerate(lines):
          if line.startswith('MODEL_ENDPOINT='):
            lines[i] = f'MODEL_ENDPOINT={selected_endpoint}\n'
            updated = True
            break

        if not updated:
          lines.append(f'MODEL_ENDPOINT={selected_endpoint}\n')

        # Write back to .env
        with open(env_file, 'w') as f:
          f.writelines(lines)
      else:
        # Create .env file
        with open(env_file, 'w') as f:
          f.write(f'MODEL_ENDPOINT={selected_endpoint}\n')

      console.print('')
      console.print(f'✅ Model endpoint configured: {selected_endpoint}')
      console.print('   This will be used for AI analysis features.')
      console.print('')

      return True

    except subprocess.TimeoutExpired:
      console.print('⚠️  Timeout fetching endpoints. You can configure this manually later.')
      return True
    except json.JSONDecodeError:
      console.print('⚠️  Error parsing endpoint data. You can configure this manually later.')
      return True
    except Exception as e:
      console.print(f'⚠️  Error during endpoint setup: {e}')
      console.print('   You can configure this manually later by editing .env')
      return True

  def initialize_review_app(self) -> bool:
    """Initialize review app for the experiment (auto-creates if doesn't exist)."""
    console.print('\n🔬 Initializing review app for experiment...')

    if not self.experiment_id:
      console.print('❌ No experiment ID available for review app initialization')
      return False

    try:
      # Run the get_review_app tool which auto-creates if doesn't exist
      cmd = [
        'uv',
        'run',
        'python',
        'tools/get_review_app.py',
        '--experiment-id',
        self.experiment_id,
      ]

      success, output = self.run_command(cmd, timeout=60)

      if success:
        try:
          # Parse the JSON output to verify review app was found/created
          review_app_data = json.loads(output)
          if review_app_data and 'id' in review_app_data:
            review_app_id = review_app_data['id']
            console.print(f'✅ Review app initialized: {review_app_id}')
            console.print(f'   Experiment ID: {self.experiment_id}')
            return True
          else:
            console.print('⚠️  Review app data is empty or invalid')
            return False
        except json.JSONDecodeError:
          console.print('⚠️  Could not parse review app response as JSON')
          console.print(f'   Output: {output}')
          return False
      else:
        console.print(f'❌ Failed to initialize review app: {output}')
        return False

    except Exception as e:
      console.print(f'❌ Error initializing review app: {e}')
      return False

  def verify_all_permissions_post_deployment(self) -> bool:
    """Verify and fix permissions for developers and service principal after deployment."""
    try:
      if not self.experiment_id:
        console.print('⚠️ No experiment ID configured, skipping permission verification')
        return True

      console.print('Checking experiment permissions for all principals...')

      # Get current experiment permissions
      permissions_data = get_experiment_permissions(
        self.experiment_id, self.auth_type, self.profile
      )

      if 'error' in permissions_data:
        console.print(f'❌ Failed to get experiment permissions: {permissions_data["error"]}')
        return False

      # Get app status to find service principal
      app_status = get_app_status(self.app_name, self.auth_type, self.profile)
      service_principal_name = (
        app_status.get('service_principal_name', '') if 'error' not in app_status else ''
      )
      service_principal_id = (
        app_status.get('service_principal_client_id', '') if 'error' not in app_status else ''
      )  # UUID for permissions API

      # Load developers from config.yaml
      config = self.load_config_yaml()
      developers = config.get('developers', [])

      # Parse current permissions
      access_control_list = permissions_data.get('access_control_list', [])
      current_permissions = {}

      for acl in access_control_list:
        principal = (
          acl.get('service_principal_name') or acl.get('user_name') or acl.get('group_name')
        )
        if principal:
          permissions = acl.get('all_permissions', [])
          permission_levels = [p.get('permission_level', 'Unknown') for p in permissions]
          current_permissions[principal] = permission_levels

      # Check each developer
      console.print('\n👥 DEVELOPER PERMISSIONS:')
      console.print('-' * 25)
      developers_needing_access = []

      for dev_email in developers:
        has_manage = 'CAN_MANAGE' in current_permissions.get(dev_email, [])
        if has_manage:
          console.print(f'✅ {dev_email}: CAN_MANAGE')
        else:
          console.print(f'❌ {dev_email}: MISSING CAN_MANAGE')
          developers_needing_access.append(dev_email)

      # Check service principal
      console.print('\n🤖 SERVICE PRINCIPAL PERMISSIONS:')
      console.print('-' * 35)
      sp_needs_access = False

      if service_principal_name:
        # Check by UUID since that's what the permissions API returns
        has_manage = 'CAN_MANAGE' in current_permissions.get(service_principal_id, [])
        if has_manage:
          console.print(f'✅ {service_principal_name}: CAN_MANAGE')
        else:
          console.print(f'❌ {service_principal_name}: MISSING CAN_MANAGE')
          sp_needs_access = True
      else:
        console.print('⚠️ Could not determine service principal name')

      # Grant permissions if needed
      if developers_needing_access or sp_needs_access:
        console.print('\n⚠️ Some principals are missing CAN_MANAGE permissions!')

        principals_to_grant = []
        if developers_needing_access:
          console.print(f'   Developers needing access: {", ".join(developers_needing_access)}')
          principals_to_grant.extend([('user', dev) for dev in developers_needing_access])
        if sp_needs_access:
          console.print(f'   Service principal needing access: {service_principal_name}')
          # Use UUID for service principal API calls
          principal_id = service_principal_id if service_principal_id else service_principal_name
          principals_to_grant.append(('service_principal', principal_id))

        if Confirm.ask('\n🔧 Grant CAN_MANAGE permissions to these principals?', default=True):
          console.print('\nGranting permissions...')

          success_count = 0
          for principal_type, principal_id in principals_to_grant:
            if self.grant_permission_to_principal(principal_type, principal_id):
              console.print(f'✅ Granted CAN_MANAGE to {principal_id}')
              success_count += 1
            else:
              console.print(f'❌ Failed to grant permission to {principal_id}')

          if success_count > 0:
            # Re-verify permissions
            console.print('\n🔍 RE-VERIFYING PERMISSIONS:')
            console.print('-' * 30)

            updated_permissions = get_experiment_permissions(
              self.experiment_id, self.auth_type, self.profile
            )

            if 'error' not in updated_permissions:
              access_control_list = updated_permissions.get('access_control_list', [])
              updated_perms = {}

              for acl in access_control_list:
                principal = (
                  acl.get('service_principal_name') or acl.get('user_name') or acl.get('group_name')
                )
                if principal:
                  permissions = acl.get('all_permissions', [])
                  permission_levels = [p.get('permission_level', 'Unknown') for p in permissions]
                  updated_perms[principal] = permission_levels

              # Show updated developer permissions
              console.print('\n👥 Updated Developer Permissions:')
              for dev_email in developers:
                has_manage = 'CAN_MANAGE' in updated_perms.get(dev_email, [])
                if has_manage:
                  console.print(f'   ✅ {dev_email}: CAN_MANAGE')
                else:
                  console.print(f'   ❌ {dev_email}: STILL MISSING')

              # Show updated service principal permissions
              if service_principal_name:
                console.print('\n🤖 Updated Service Principal Permissions:')
                # Check by UUID since that's what the permissions API returns
                has_manage = 'CAN_MANAGE' in updated_perms.get(service_principal_id, [])
                if has_manage:
                  console.print(f'   ✅ {service_principal_name}: CAN_MANAGE')
                else:
                  console.print(f'   ❌ {service_principal_name}: STILL MISSING')
            else:
              console.print('⚠️ Could not verify updated permissions')
        else:
          console.print('⚠️ Skipping permission grants. You can grant them manually later.')
      else:
        console.print('\n✅ All principals have correct CAN_MANAGE permissions!')

      return True

    except Exception as e:
      console.print(f'❌ Error verifying permissions: {e}')
      return False

  def grant_permission_to_principal(self, principal_type: str, principal_id: str) -> bool:
    """Grant CAN_MANAGE permission to a specific principal."""
    try:
      cmd = [
        'uv',
        'run',
        'python',
        'tools/grant_experiment_permissions.py',
        '--experiment-id',
        self.experiment_id,
        '--principal-type',
        principal_type,
        '--principal-id',
        principal_id,
        '--permission',
        'CAN_MANAGE',
      ]

      success, output = self.run_command(cmd, timeout=60)
      return success

    except Exception as e:
      console.print(f'❌ Error granting permission: {e}')
      return False

  def check_workspace_obo_status(self) -> bool:
    """Check workspace OBO status before deployment."""
    console.print('\n🔍 Checking workspace OBO (On-Behalf-Of) configuration...')

    try:
      result = get_workspace_obo_status(self.auth_type, self.profile)

      if 'error' in result:
        console.print(f'⚠️  Could not determine workspace OBO status: {result["error"]}')
        self.workspace_obo_enabled = None
      else:
        workspace_id = result.get('workspace_id', 'Unknown')
        obo_enabled = result.get('obo_enabled', False)

        console.print(f'🏢 Workspace ID: {workspace_id}')
        console.print(f'🔒 Workspace OBO Status: {"ENABLED" if obo_enabled else "DISABLED"}')

        self.workspace_obo_enabled = obo_enabled

        if not obo_enabled:
          console.print('\n❌ OBO is currently DISABLED in workspace preview features')
          console.print('🚨 ERROR: OBO is REQUIRED for this app to function properly!')
          console.print('')
          console.print('📋 Please enable OBO now:')
          console.print('1. Visit workspace settings:')
          if self.workspace_host:
            console.print(f'   {self.workspace_host}/settings/workspace/preview')
          else:
            console.print(
              '   https://your-workspace.cloud.databricks.com/settings/workspace/preview'
            )
          console.print("2. Look for 'On-behalf-of authentication' and enable it")
          console.print('3. Come back here when enabled')
          console.print('')

          # Wait for user to enable OBO
          while True:
            if Confirm.ask('Have you enabled OBO in workspace preview features?', default=True):
              break
            else:
              console.print('💡 Please enable OBO to continue setup. This is required.')
              continue

            console.print('🔍 Re-checking workspace OBO status...')
            # Re-check OBO status
            recheck_result = get_workspace_obo_status(self.auth_type, self.profile)
            if not recheck_result.get('error') and recheck_result.get('obo_enabled', False):
              console.print('✅ OBO is now enabled in workspace!')
              self.workspace_obo_enabled = True

              # Restart the app immediately after OBO is enabled
              if self.app_name:
                console.print('🔄 Restarting app to enable user authentication...')
                console.print('⏰ This will take 2-3 minutes...')
                if self.restart_app():
                  console.print('✅ App restarted successfully with OBO enabled!')
                else:
                  console.print('⚠️  App restart failed. You may need to restart manually later.')

              break
            else:
              console.print("❌ OBO still appears to be disabled. Please ensure it's enabled.")
              continue
        else:
          console.print('✅ Workspace OBO is enabled - user authentication will work!')

      return True

    except Exception as e:
      console.print(f'⚠️  Could not check workspace OBO status: {e}')
      self.workspace_obo_enabled = None
      return True  # Continue setup even if OBO check fails

  def deploy_app(self) -> bool:
    """Deploy the Databricks app."""
    console.print('\n🚀 Deploying app to ensure latest code is available...')
    console.print('📋 Running: ./deploy.sh --create')
    console.print('')

    try:
      # Run deploy script with real-time output
      process = subprocess.Popen(
        ['./deploy.sh', '--create'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
      )

      output_lines = []
      while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
          break
        if output:
          line = output.strip()
          output_lines.append(line)
          console.print(f'   {line}')

      return_code = process.poll()

      if return_code == 0:
        console.print('')
        console.print('✅ App deployed successfully!')
        return True
      else:
        console.print('')
        console.print('❌ Deployment failed!')
        console.print('\n📋 To retry deployment manually:')
        console.print('   ./deploy.sh --create')
        return False

    except Exception as e:
      console.print(f'❌ Error running deployment: {e}')
      console.print('\n📋 To retry deployment manually:')
      console.print('   ./deploy.sh --create')
      return False

  def restart_app(self) -> bool:
    """Restart the Databricks app to pick up OBO configuration changes."""
    if not self.app_name:
      console.print('❌ No app name available for restart')
      return False

    console.print('\n🔄 Restarting app to enable user authorization...')

    # Stop the app
    console.print('⏹️  Stopping app...')
    cmd = ['databricks', 'apps', 'stop', self.app_name]
    if self.auth_type == 'profile' and self.profile:
      cmd.extend(['--profile', self.profile])

    success, output = self.run_command(cmd, timeout=60)
    if not success:
      console.print(f'⚠️  Failed to stop app: {output}')
      console.print('💡 You may need to stop the app manually in the Databricks UI')
      return False

    console.print('✅ App stopped successfully')

    # Start the app
    console.print('▶️  Starting app...')
    cmd = ['databricks', 'apps', 'start', self.app_name]
    if self.auth_type == 'profile' and self.profile:
      cmd.extend(['--profile', self.profile])

    success, output = self.run_command(cmd, timeout=120)  # Apps can take longer to start
    if success:
      console.print('✅ App restarted successfully!')
      console.print('🎉 User authorization (OBO) should now be active!')
      return True
    else:
      console.print(f'⚠️  Failed to start app: {output}')
      console.print('💡 You may need to start the app manually in the Databricks UI')
      return False

  def check_service_principal_permissions(self) -> bool:
    """Check and configure service principal permissions."""
    console.print('\n🔑 Checking service principal permissions...')

    if not self.experiment_id:
      console.print('💡 Experiment ID will be configured in Review App setup section')
      return True

    try:
      # Get app status
      app_status = get_app_status(self.app_name, self.auth_type, self.profile)

      if 'error' in app_status:
        console.print(f'❌ Could not get app status: {app_status["error"]}')
        return False

      # Get experiment permissions
      permissions_data = get_experiment_permissions(
        self.experiment_id, self.auth_type, self.profile
      )
      permissions_check = check_user_authorization_sp_permissions(permissions_data, app_status)

      if 'error' in permissions_check:
        console.print(f'❌ Could not check permissions: {permissions_check["error"]}')
        return False

      # Analyze permissions
      primary_sp = permissions_check.get('primary_service_principal', {})
      service_client_id = primary_sp.get('id', '')
      has_permissions = primary_sp.get('found', False)

      # The service principal should be the app name, not a UUID
      # Let's also show what we got from app status for debugging
      service_principal_name = app_status.get('service_principal_name', '')

      console.print(f'🔑 App Service Principal: {service_principal_name}')
      if service_client_id != service_principal_name and service_client_id:
        console.print(f'🔑 Service Principal Client ID: {service_client_id}')

      if has_permissions:
        permissions_str = ', '.join(primary_sp.get('permissions', []))
        console.print(f'✅ Service principal has permissions: {permissions_str}')

        # Final status - OBO should already be enabled at this point
        console.print('\n🎉 Service principal permissions configured!')

        if self.workspace_obo_enabled is True:
          console.print('✅ OBO is enabled - app is fully configured!')
          app_url = app_status.get('url', '')
          if app_url:
            console.print(f'🚀 Your app is ready at: {app_url}')
        else:
          console.print('⚠️  OBO status unknown, but service principal permissions are configured')

        return True
      else:
        console.print('❌ Service principal does NOT have experiment permissions')
        console.print("\n🚨 IMPORTANT: To enable OBO functionality, the app's service principal")
        console.print('   needs write access to the MLflow experiment.')

        if Confirm.ask('Would you like to grant permissions automatically?', default=True):
          console.print('\n🔧 Granting CAN_MANAGE permissions to service principal...')

          # Use grant_experiment_permissions tool
          cmd = [
            'uv',
            'run',
            'python',
            'tools/grant_experiment_permissions.py',
            '--principal-id',
            service_client_id,
            '--principal-type',
            'service_principal',
            '--permission',
            'CAN_MANAGE',
            '--experiment-id',
            self.experiment_id,
            '--format',
            'json',
          ]

          success, output = self.run_command(cmd)

          if success:
            try:
              result = json.loads(output)
              if result.get('success', False):
                console.print('✅ Successfully granted experiment permissions!')
                return True
              else:
                console.print(
                  f'❌ Failed to grant permissions: {result.get("error", "Unknown error")}'
                )
            except json.JSONDecodeError:
              console.print('❌ Failed to parse permission grant result')
          else:
            console.print(f'❌ Error granting permissions: {output}')

        # Show manual instructions
        console.print('\n📋 Manual steps to grant permissions:')
        console.print('1. Open your MLflow experiment in Databricks:')
        if self.workspace_host:
          console.print(f'   {self.workspace_host}/ml/experiments/{self.experiment_id}')
        console.print("2. Click the 'Permissions' tab")
        console.print("3. Click 'Add permissions'")
        console.print(f'4. Add service principal: {service_client_id}')
        console.print("5. Grant 'Can Manage' permissions")

        return False

    except Exception as e:
      console.print(f'❌ Error checking service principal permissions: {e}')
      return False

  def run(self):
    """Main setup workflow with clearly delineated sections."""
    try:
      console.print('🚀 Databricks App Template Setup')
      console.print('=' * 50)
      console.print('')

      # ===============================================
      # SECTION A: ENVIRONMENT SETUP
      # ===============================================
      console.print('🌍 SECTION A: ENVIRONMENT SETUP')
      console.print('=' * 35)

      # Install development tools
      self.install_tools()

      # Load or create authentication configuration
      if not self.load_existing_config():
        console.print('✅ Using existing configuration')
        self.env_vars = load_env_local()
        self.auth_type = self.env_vars.get('DATABRICKS_AUTH_TYPE')
        self.profile = self.env_vars.get('DATABRICKS_CONFIG_PROFILE')
        self.workspace_host = self.env_vars.get('DATABRICKS_HOST')
        self.app_name = self.env_vars.get('DATABRICKS_APP_NAME')
      else:
        # Set up authentication
        if not self.setup_authentication():
          raise SetupError('Authentication setup failed')

      # Get user info (needed for both existing and new configs)
      username = self.get_current_user_info()
      if not username:
        console.print('⚠️  Could not determine current user')
        username = None

      console.print('✅ Environment setup complete')
      console.print('')

      # ===============================================
      # SECTION B: APP SETUP
      # ===============================================
      console.print('📱 SECTION B: APP SETUP')
      console.print('=' * 25)

      # Check existing app status if app name is defined
      if self.app_name:
        console.print('\n📊 Checking existing app status...')
        app_status = get_app_status(self.app_name, self.auth_type, self.profile)

        if 'error' not in app_status:
          # Display app status
          app_state = app_status.get('app_status', {}).get('state', 'Unknown')
          app_message = app_status.get('app_status', {}).get('message', 'No message')
          app_url = app_status.get('url', 'Not available')
          service_principal = app_status.get('service_principal_name', 'Not available')

          # Determine status emoji
          if app_state == 'RUNNING':
            status_emoji = '✅'
          elif app_state == 'UNAVAILABLE':
            status_emoji = '❌'
          elif app_state == 'STARTING':
            status_emoji = '⏳'
          else:
            status_emoji = '❓'

          console.print(f'\n{status_emoji} App Status: {app_state}')
          console.print(f'   Name: {self.app_name}')
          console.print(f'   URL: {app_url}')
          console.print(f'   Service Principal: {service_principal}')
          if app_message and app_message != 'No message':
            console.print(f'   Message: {app_message}')

          # Show compute status
          compute_status = app_status.get('compute_status', {})
          compute_state = compute_status.get('state', 'Unknown')
          if compute_state == 'ACTIVE':
            compute_emoji = '✅'
          elif compute_state == 'INACTIVE':
            compute_emoji = '❌'
          elif compute_state == 'STARTING':
            compute_emoji = '⏳'
          else:
            compute_emoji = '❓'

          console.print(f'{compute_emoji} Compute Status: {compute_state}')
          if compute_status.get('message'):
            console.print(f'   Message: {compute_status.get("message")}')
          console.print('')
        else:
          console.print(f'⚠️  Could not get app status: {app_status.get("error")}')
          console.print('   The app may not exist yet or you may not have access.')
          console.print('')

      # Configure app settings - always ask if user wants to change
      if not self.setup_app_configuration(username):
        raise SetupError('App configuration failed')

      # Check workspace OBO status (required for app functionality)
      if not self.check_workspace_obo_status():
        console.print('⚠️  OBO check failed, but continuing with setup...')

      console.print('✅ App setup complete')
      console.print('')

      # ===============================================
      # SECTION C: REVIEW APP SETUP
      # ===============================================
      console.print('🔬 SECTION C: REVIEW APP SETUP')
      console.print('=' * 30)

      # Configure MLflow experiment (includes developer management)
      if not self.setup_mlflow_experiment():
        raise SetupError('MLflow experiment setup failed')

      # Configure AI model endpoint for analysis (optional)
      if not self.setup_model_endpoint():
        console.print('⚠️  Model endpoint setup had issues, but continuing with setup...')

      # Initialize review app for the experiment (auto-creates if doesn't exist)
      if not self.initialize_review_app():
        console.print('⚠️  Review app initialization failed, but continuing with setup...')

      console.print('✅ Review app setup complete')
      console.print('')

      # ===============================================
      # FINAL DEPLOYMENT
      # ===============================================
      console.print('🚀 FINAL DEPLOYMENT')
      console.print('=' * 20)
      console.print('All configuration is complete. Ready to deploy the app.')
      console.print('')

      # Deploy the app with complete configuration
      if not self.deploy_app():
        console.print(
          '⚠️  Deployment failed, but you can deploy manually later with: ./deploy.sh --create'
        )
      else:
        console.print('✅ App deployed successfully!')

        # ===============================================
        # DEPLOYMENT VERIFICATION
        # ===============================================
        console.print('\n🔍 DEPLOYMENT VERIFICATION')
        console.print('=' * 27)
        console.print('Verifying all permissions after deployment...')
        self.verify_all_permissions_post_deployment()

      console.print('')

      # ===============================================
      # SETUP COMPLETE
      # ===============================================
      console.print('🎉 SETUP COMPLETE!')
      console.print('=' * 20)
      console.print('')
      if RICH_AVAILABLE:
        console.print(
          '⚠️  IMPORTANT: Please restart Claude Code to enable MCP Playwright integration'
        )
      else:
        console.print("💡 Consider installing 'rich' for better setup experience: uv add rich")
      console.print('')
      console.print('Next steps:')
      console.print('1. Restart Claude Code (close and reopen the application)')
      console.print("2. Run './watch.sh' to start the development servers")
      console.print('3. Open http://localhost:5173 to view the app')
      console.print('4. Open http://localhost:8000/docs to view the API documentation')
      console.print('')
      console.print('Optional:')
      console.print("- Run './fix.sh' to format your code")
      console.print('- Edit .env.local to update configuration')
      console.print("- Run 'uv run python app_status.py' to check deployment status")

    except SetupError as e:
      console.print(f'❌ Setup failed: {e}')
      return 1
    except KeyboardInterrupt:
      console.print('\n⚠️  Setup interrupted by user')
      return 1
    except Exception as e:
      console.print(f'❌ Unexpected error: {e}')
      console.print(f'   {type(e).__name__}: {str(e)}')
      return 1
    finally:
      self.cleanup()

    return 0


def main():
  """Main entry point."""
  parser = argparse.ArgumentParser(description='Interactive Databricks App setup')
  parser.add_argument(
    '--auto-close', action='store_true', help='Auto-close terminal after completion'
  )
  parser.add_argument('--temp-file', help='Temporary file for completion signal')
  args = parser.parse_args()

  setup = DatabricksAppSetup(auto_close=args.auto_close, temp_file=args.temp_file)
  return setup.run()


if __name__ == '__main__':
  sys.exit(main())
