# MLflow Review App - Playwright Testing Plan

This document provides a step-by-step testing workflow for the MLflow Review App using Playwright browser automation. The workflow covers the complete lifecycle from creating a labeling session as a developer to collecting labels as an SME and reviewing the results.

## Prerequisites

1. The development server should be running (`./watch.sh`)
2. A review app should already exist for the experiment
3. Playwright should be available in the Claude environment

## Testing Workflow

### Part A: Developer Creates a Labeling Session

1. **Navigate to Developer Dashboard**

   - Open the browser to `http://localhost:5173/dev` (or the appropriate port)
   - Wait for the page to load completely
   - Verify that the experiment name and ID are displayed

2. **Create a New Labeling Session**

   - Click the "Create Session" button in the Labeling Sessions section
   - A dialog should open with fields for session name and assigned users
   - Enter a descriptive session name (e.g., "QA Review Session - Week 1")
   - Enter one or more email addresses separated by commas (e.g., "sme1@example.com, sme2@example.com")
   - Click the "Create Session" button in the dialog
   - Wait for the session to be created
   - Verify the new session appears in the sessions list with:
     - The session name you entered
     - A unique session ID
     - An MLflow run ID
     - The assigned users displayed as badges

3. **Note the Session Details**
   - Take note of the session ID and MLflow run ID for later verification
   - Verify that the session ID and run ID are clickable links

### Part B: SME Labels Traces

4. **Navigate to Labeling Page as SME**

   - Navigate to the root URL `http://localhost:5173/`
   - The page should show "Your Labeling Sessions"
   - Verify that the newly created session appears in the list
   - The session should show it's assigned to the current user

5. **Start Labeling Session**

   - Click the "Start Labeling" button for the session
   - The browser should navigate to the review app page
   - Wait for the page to load completely

6. **Review and Label Traces**

   - The page should display:
     - Session information at the top
     - Navigation controls (Previous/Next buttons)
     - Current trace information
     - Chat conversation display
     - Labeling form with schemas (e.g., Response Quality, Helpfulness)

7. **Submit Labels for Multiple Traces**

   - For the first trace:

     - Review the conversation in the chat display
     - Select a rating for "Response Quality" (e.g., "Good")
     - Select a rating for "Helpfulness" (e.g., "Very Helpful")
     - Optionally add a comment
     - Click "Submit & Next"

   - For the second trace:

     - Verify the UI updates to show the next trace
     - Select different ratings to test variety
     - Add a detailed comment
     - Click "Submit & Next"

   - Continue for at least 3-5 traces to create meaningful test data

8. **Verify Progress Tracking**
   - Check that the progress indicator updates (e.g., "3 of 10 traces")
   - Verify that submitted traces show a checkmark or completed status
   - Test the "Previous" button to go back to a labeled trace
   - Verify that previous labels are displayed when revisiting

### Part C: Developer Reviews Labels

9. **Return to Developer Dashboard**

   - Navigate back to `http://localhost:5173/dev`
   - Locate the labeling session that was just used

10. **Access MLflow Labeling Session**

    - Click on the Session ID link
    - This should open the MLflow UI in a new tab showing the labeling session
    - Verify that the session contains the labels that were submitted

11. **Access MLflow Run**

    - Back in the Developer Dashboard, click on the MLflow Run ID link
    - This should open the MLflow evaluation runs page
    - Verify that the run contains:
      - The submitted labels as metrics or artifacts
      - Trace linkage information
      - Timestamps matching when labels were submitted

12. **Verify Data Persistence**
    - Refresh the Developer Dashboard
    - Ensure all session information is still present
    - Navigate to the SME labeling page and verify completed sessions show progress

## Advanced Testing Scenarios

### Multiple SMEs

1. Create a session with multiple assigned users
2. Test that each user sees the session in their labeling page
3. Verify that labels from different users are tracked separately

### Edge Cases

1. Test submitting labels without selecting all required fields
2. Test navigation when at the first/last trace
3. Test browser refresh during labeling session
4. Test very long comments or special characters in labels

### Performance Testing

1. Create a session linked to many traces (50+)
2. Verify that navigation between traces remains responsive
3. Check that label submission doesn't slow down over time

## Expected Outcomes

- Developers can create labeling sessions with specific SME assignments
- SMEs see only their assigned sessions
- Labels are properly saved and linked to MLflow runs
- All data persists across page refreshes
- Navigation to MLflow UI works correctly with proper deep links
- The workflow supports multiple concurrent labeling sessions

## Troubleshooting

If any step fails:

1. Check the browser console for errors
2. Verify the development server is running (`tail -f /tmp/databricks-app-watch.log`)
3. Ensure all API endpoints are responding (check Network tab)
4. Verify that the MLflow experiment exists and is accessible

## Notes for Automation

When implementing this as an automated Playwright test:

- Use `page.waitForSelector()` to ensure elements are loaded before interaction
- Add appropriate delays after API calls to allow for data updates
- Take screenshots at key points for debugging
- Use data attributes or specific text content for reliable element selection
- Consider using test-specific email addresses and session names with timestamps
