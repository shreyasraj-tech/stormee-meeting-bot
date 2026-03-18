
# ECG Changes Summary

## Feature: Automated Meeting Summarization and Email Delivery

### Summary of Changes:

Implemented an end-to-end automated meeting summarization and email delivery system that captures meeting transcripts, generates AI-powered summaries using the eCG.AI API, and delivers results via email. The system includes both automated detection of meeting end (based on participant count) and manual override capabilities.

### ACTs Implemented:

- **ACT 1:** Add Required Dependencies to package.json
  - Added `axios`, `nodemailer`, and `html-to-text` dependencies to enable API communication and email functionality.

- **ACT 2:** Create eCG.AI Summarization Service
  - Created `services/ecgService.js` with `getMeetingSummary` function to interact with the eCG.AI API for transcript summarization.

- **ACT 3:** Create Email Delivery Service
  - Created `services/emailService.js` with `sendSummary` function to handle email formatting and delivery with OAuth and SMTP authentication support.

- **ACT 4:** Enhance Meeting Bot with Transcript Capture and Participant Monitoring
  - Modified `services/meetBot.js` to capture meeting transcripts, implement participant monitoring, and provide functions for managing the monitoring lifecycle.

- **ACT 5:** Create End-of-Meeting Controller and Integrate Services
  - Modified `controllers/meetController.js` to add `endMeetingController` that orchestrates the complete end-of-meeting workflow.

- **ACT 6:** Add Manual Override Route for Meeting End
  - Modified `routes/meetRoutes.js` to add the `POST /api/end-meeting` route for manual meeting termination and summary delivery.

### Key Features Implemented:

1. **Transcript Capture:** Meeting captions are automatically captured and stored in a structured format with speaker identification.

2. **Automated Meeting End Detection:** The system monitors participant count every 5 seconds and triggers the end-of-meeting workflow when only 1 participant remains for 30+ seconds.

3. **AI-Powered Summarization:** Meeting transcripts are sent to the eCG.AI API to generate summaries and extract action items.

4. **Email Delivery:** Summaries are formatted as HTML emails and delivered via Gmail using either OAuth2 tokens or SMTP credentials.

5. **Manual Override:** Users can trigger the end-of-meeting workflow manually via the `/api/end-meeting` POST endpoint.

### Environment Variables Required:

- `ECG_API_KEY`: API key for eCG.AI service
- `EMAIL_USER`: Gmail account email address
- `EMAIL_PASS`: Gmail app password (for SMTP fallback)
- `GOOGLE_CLIENT_ID`: Google OAuth client ID (for OAuth authentication)
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret (for OAuth authentication)

### Files Modified/Created:

- `package.json` - Added dependencies
- `services/ecgService.js` - New file
- `services/emailService.js` - New file
- `services/meetBot.js` - Enhanced with transcript capture and monitoring
- `controllers/meetController.js` - Added end-of-meeting orchestration
- `routes/meetRoutes.js` - Added manual override route

