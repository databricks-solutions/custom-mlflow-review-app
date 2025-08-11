#!/usr/bin/env python3
"""Test MLflow assessment update functionality directly using MLflow SDK."""

import os
from datetime import datetime

import mlflow
from dotenv import load_dotenv
from mlflow import MlflowClient
from mlflow.entities.assessment import AssessmentSource, AssessmentSourceType

# Load environment variables
load_dotenv('.env.local')

# Set MLflow tracking URI and environment
databricks_host = os.getenv('DATABRICKS_HOST')
databricks_token = os.getenv('DATABRICKS_TOKEN')

if not databricks_host or not databricks_token:
  print('ERROR: DATABRICKS_HOST and DATABRICKS_TOKEN must be set in .env.local')
  exit(1)

print(f'Using Databricks Host: {databricks_host[:30]}...')

# Configure MLflow for Databricks
os.environ['DATABRICKS_HOST'] = databricks_host
os.environ['DATABRICKS_TOKEN'] = databricks_token
mlflow.set_tracking_uri('databricks')


def test_assessment_update():
  """Test the assessment update flow using MLflow SDK directly."""
  # Test configuration
  trace_id = 'tr-3323be404e0e74fc56a4c18e401d5ed0'
  assessment_name = 'test_direct_update'
  initial_value = 'Initial'
  updated_value = 'Updated'

  client = MlflowClient()

  print(f"\n{'='*60}")
  print('Testing MLflow Assessment Update (Direct SDK)')
  print(f"{'='*60}")
  print(f'Trace ID: {trace_id}')
  print(f'Timestamp: {datetime.now().isoformat()}')

  # First verify the trace exists
  print('\n0. Verifying trace exists...')
  try:
    trace = client.get_trace(trace_id)
    if trace:
      print('   ✓ Trace found')
    else:
      print('   ✗ Trace is None!')
      return False
  except Exception as e:
    print(f'   ✗ Failed to get trace: {e}')
    return False

  # Step 1: Create initial assessment using SDK
  print('\n1. Creating initial assessment with MLflow SDK...')
  print(f'   Name: {assessment_name}')
  print(f'   Value: {initial_value}')

  try:
    # Create the assessment using mlflow module with keyword arguments
    assessment = mlflow.log_feedback(
      trace_id=trace_id,
      name=assessment_name,
      value=initial_value,
      source=AssessmentSource(source_type=AssessmentSourceType.HUMAN, source_id='test_user'),
      rationale='Initial test assessment',
    )

    print('   ✓ Assessment created successfully')
    print(f'   Assessment ID: {assessment.assessment_id}')
    print(f'   Assessment type: {type(assessment)}')
    print(f'   Assessment attributes: {dir(assessment)}')
    assessment_id = assessment.assessment_id

  except Exception as e:
    print(f'   ✗ Failed to create assessment: {e}')
    print(f'   Error type: {type(e).__name__}')
    return False

  # Step 2: Update the assessment using SDK
  print('\n2. Updating assessment with MLflow SDK...')
  print(f'   Assessment ID: {assessment_id}')
  print(f'   New Value: {updated_value}')

  try:
    # Try mlflow.update_assessment by modifying the existing assessment
    print('   Trying mlflow.update_assessment...')

    # First get the current assessment object from the trace
    trace_for_update = client.get_trace(trace_id)
    current_assessment = None
    for assess in trace_for_update.info.assessments:
      if getattr(assess, 'assessment_id', None) == assessment_id:
        current_assessment = assess
        break

    if current_assessment:
      print('   Found current assessment to update')
      print(f'   Current assessment type: {type(current_assessment)}')

      # Try creating a minimal assessment with just what we want to update
      from mlflow.entities.assessment import Feedback

      # Create just a Feedback object with new value
      new_feedback = Feedback(value=updated_value, rationale='Updated test assessment')

      print(f'   Created new feedback object: {new_feedback}')

      try:
        # Try passing just the feedback object
        mlflow.update_assessment(trace_id, assessment_id, new_feedback)
        print('   ✓ update_assessment succeeded')
      except Exception as e1:
        print(f'   update_assessment failed: {e1}')
        print('   Trying different approach...')

        # Try direct attribute update approach
        try:
          # Update value in the current assessment's feedback
          if hasattr(current_assessment, 'feedback') and current_assessment.feedback:
            current_assessment.feedback.value = updated_value
            if hasattr(current_assessment.feedback, 'rationale'):
              current_assessment.feedback.rationale = 'Updated test assessment'

          # Remove the name field to prevent the error
          temp_name = current_assessment.name
          current_assessment.name = None

          mlflow.update_assessment(trace_id, assessment_id, current_assessment)
          print('   ✓ update_assessment succeeded with workaround')

          # Restore name
          current_assessment.name = temp_name

        except Exception as e2:
          print(f'   Second approach also failed: {e2}')
          return False
    else:
      print('   ✗ Could not find current assessment to modify')
      return False

    print('   ✓ Assessment update call succeeded')

  except Exception as e:
    print(f'   ✗ Failed to update assessment: {e}')
    print(f'   Error type: {type(e).__name__}')
    return False

  # Step 3: Verify the update by getting the trace
  print('\n3. Verifying update by getting trace...')

  try:
    # Get the trace
    trace = client.get_trace(trace_id)

    # Find our assessment
    found_assessment = None
    all_assessments = []

    if hasattr(trace.info, 'assessments') and trace.info.assessments:
      for assessment in trace.info.assessments:
        # Collect all assessments for debugging
        assessment_info = {
          'id': getattr(assessment, 'assessment_id', 'N/A'),
          'name': getattr(assessment, 'name', 'N/A'),
          'value': None,
          'is_invalid': getattr(assessment, 'is_invalid', False),
        }

        # Get value from feedback or expectation
        if hasattr(assessment, 'feedback') and assessment.feedback:
          assessment_info['value'] = assessment.feedback.value
          assessment_info['type'] = 'feedback'
        elif hasattr(assessment, 'expectation') and assessment.expectation:
          assessment_info['value'] = assessment.expectation.value
          assessment_info['type'] = 'expectation'

        all_assessments.append(assessment_info)

        # Check if this is our assessment (and not invalidated)
        if getattr(assessment, 'assessment_id', None) == assessment_id:
          if not getattr(assessment, 'is_invalid', False):
            found_assessment = assessment_info

    if found_assessment:
      print(f'   ✓ Assessment found with ID: {assessment_id}')
      print(f"   Current value: {found_assessment['value']}")

      if found_assessment['value'] == updated_value:
        print('\n   ✅ SUCCESS: MLflow override_feedback WORKS!')
        print(f'      Expected: {updated_value}')
        print(f"      Actual: {found_assessment['value']}")
        return True
      else:
        print('\n   ❌ FAILURE: MLflow override_feedback DOES NOT WORK!')
        print(f'      Expected: {updated_value}')
        print(f"      Actual: {found_assessment['value']}")
        print(
          "\n   This means MLflow's override_feedback API is broken or creates new assessments instead of updating!"
        )
        return False
    else:
      print(f'   ✗ Assessment with ID {assessment_id} not found or was invalidated')
      print('\n   All assessments in trace:')
      for idx, assessment in enumerate(all_assessments, 1):
        invalid_marker = ' [INVALID]' if assessment.get('is_invalid') else ''
        print(
          f"     [{idx}] ID: {assessment['id']}, Name: {assessment['name']}, Value: {assessment['value']}{invalid_marker}"
        )
      return False

  except Exception as e:
    print(f'   ✗ Failed to verify: {e}')
    print(f'   Error type: {type(e).__name__}')
    return False

  finally:
    print(f"\n{'='*60}\n")


if __name__ == '__main__':
  success = test_assessment_update()
  if not success:
    print("⚠️  MLflow's override_feedback API appears to be broken!")
    print('   It may be creating new assessments instead of updating existing ones.')
  exit(0 if success else 1)
