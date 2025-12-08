
# ECG Changes Summary

## Feature: Automated Google Meet Management and Raw Data Collection

### Summary of Changes:
This feature enhances the MeetBot service with automated participant monitoring, graceful meeting exit functionality, and corresponding API endpoints. The bot can now track participant count changes in real-time, detect when it has been removed from a meeting, and exit meetings cleanly while properly managing background tasks.

### ACTs Implemented:
- **ACT 1:** Enhance Core Bot Service with Participant Counting and Monitoring
- **ACT 2:** Add Controller Functions for Participant Count and Leave Meeting
- **ACT 3:** Add API Routes for Participant Count and Leave Meeting Endpoints

### Files Modified:
- `services/stormee_meet_bot_service.py`
- `controllers/stormee_meet_bot_controller.py`
- `routes/stormee_meet_bot_routes.py`

### Key Features Added:
- Participant count retrieval with primary and fallback selectors
- Real-time participant monitoring with 15-second polling intervals
- Detection of bot removal from meetings
- Graceful meeting exit with proper resource cleanup and task cancellation
- New API endpoint: `GET /participants/count` to retrieve current participant count
- New API endpoint: `POST /leave` to command the bot to leave the meeting

### Implementation Notes:
- Participant monitoring is automatically started when the bot joins a meeting
- The monitoring task checks every 15 seconds for participant count changes
- If the bot is removed from the meeting, the monitoring task automatically triggers the leave sequence
- All background tasks (caption scraping, participant monitoring) are properly cancelled when leaving a meeting
- Error handling includes fallback selectors for participant count extraction to handle potential Google Meet UI changes
