
# ECG Changes Summary

## Feature: TaskSync Feature

### Summary of Changes:

The TaskSync feature automates the extraction of action items from meeting transcripts using OpenAI's LLM and automatically creates GitHub issues for each identified task. This integration streamlines task management by eliminating manual transcription and issue creation workflows.

### ACTs Implemented:

- **ACT 1:** Add OpenAI and Octokit Dependencies - Updates package.json to include the openai and octokit libraries required for LLM processing and GitHub integration.
- **ACT 2:** Create TaskService Module - Implements the core TaskService module that handles transcript processing with OpenAI API and GitHub issue creation.
- **ACT 3:** Integrate TaskService into meetController - Modifies the meetController to invoke TaskService after stopping captions, completing the feature integration.

### Files Modified:

- `package.json` - Modified to add new dependencies
- `services/TaskService.js` - Created new service module
- `controllers/meetController.js` - Modified to integrate TaskService

### Key Features:

- Automatic transcript processing using OpenAI LLM
- Extraction of summaries and action items from meeting transcripts
- Automatic GitHub issue creation with labels and assignees
- Configurable LLM model and GitHub repository via environment variables
- Comprehensive error handling and logging

### Environment Variables Required:

- `OPENAI_API_KEY` - API key for OpenAI
- `GITHUB_TOKEN` - Personal access token for GitHub
- `GITHUB_REPO` - GitHub repository in format owner/repo
- `LLM_MODEL` - LLM model identifier (e.g., gpt-4o)
