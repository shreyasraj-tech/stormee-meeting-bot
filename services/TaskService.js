import { OpenAI } from 'openai';
import { Octokit } from 'octokit';

// Initialize API clients
const openaiClient = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const octokitClient = new Octokit({
  auth: process.env.GITHUB_TOKEN,
});

// ---------------------------------------------------------
// CONFIGURATION & MAPPINGS
// ---------------------------------------------------------

// Map spoken names to actual GitHub usernames
const GITHUB_USER_MAP = {
  "Shreyas": "shreyas-gh-handle",
  "Alex": "alex-dev",
  "Sarah": "sarah-codes"
  // Add more team members here
};

// ---------------------------------------------------------
// CORE FUNCTIONS
// ---------------------------------------------------------

/**
 * Process meeting transcript using OpenAI LLM
 * @param {string} transcriptText - The raw text of the meeting
 * @returns {Promise<Object>} - { summary, actionItems }
 */
async function processTranscript(transcriptText) {
  console.log("🧠 Sending transcript to LLM for analysis...");

  const SYSTEM_PROMPT = `
    You are a Meeting Assistant. Your job is to extract a summary and actionable tasks.
    
    RETURN JSON ONLY. The structure must be:
    {
      "summary": "Brief summary...",
      "actionItems": [
        { 
          "task": "Action title", 
          "assignee": "Name (extracted from context)", 
          "priority": "High/Medium/Low", 
          "type": "Bug/Feature/Documentation/Other" 
        }
      ]
    }
  `;

  try {
    const response = await openaiClient.chat.completions.create({
      model: process.env.LLM_MODEL || 'gpt-4-turbo', // Turbo supports JSON mode best
      response_format: { type: "json_object" }, // <--- CRITICAL: Enforces valid JSON
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: `TRANSCRIPT:\n${transcriptText}` },
      ],
      temperature: 0.2, // Low temperature for consistent results
    });

    const parsedResponse = JSON.parse(response.choices[0].message.content);

    // Validate response
    if (!parsedResponse.actionItems || !Array.isArray(parsedResponse.actionItems)) {
      console.warn("⚠️ No action items found or invalid format.");
      parsedResponse.actionItems = [];
    }

    // Process Action Items (Parallel Execution)
    if (parsedResponse.actionItems.length > 0) {
      console.log(`🚀 syncing ${parsedResponse.actionItems.length} tasks to GitHub...`);
      await syncTasksToGitHub(parsedResponse.actionItems);
    }

    return parsedResponse;

  } catch (error) {
    console.error('❌ Error in processTranscript:', error.message);
    throw error; // Re-throw to be handled by caller
  }
}

/**
 * Handles the loop of creating multiple issues
 */
async function syncTasksToGitHub(actionItems) {
  // Use allSettled so one failure doesn't stop the others
  const results = await Promise.allSettled(
    actionItems.map(item => createGitHubIssue(item))
  );

  // Log results
  const successful = results.filter(r => r.status === 'fulfilled').length;
  const failed = results.filter(r => r.status === 'rejected').length;
  console.log(`✅ Sync Complete: ${successful} created, ${failed} failed.`);
}

/**
 * Create a single GitHub issue
 */
async function createGitHubIssue({ task, assignee, priority, type }) {
  const repoPath = process.env.GITHUB_REPO; // Format: "owner/repo"
  if (!repoPath) throw new Error('GITHUB_REPO env var missing');
  const [owner, repo] = repoPath.split('/');

  // Resolve Assignee (Name -> GitHub Username)
  const ghUsername = GITHUB_USER_MAP[assignee] || null;
  if (assignee && !ghUsername) {
    console.warn(`⚠️ Warning: Could not map name "${assignee}" to a GitHub user. Issue will be unassigned.`);
  }

  // Construct Labels
  const labels = [
    `priority: ${priority?.toLowerCase() || 'medium'}`, 
    `type: ${type?.toLowerCase() || 'task'}`,
    'bot-created'
  ];

  try {
    const issue = await octokitClient.rest.issues.create({
      owner,
      repo,
      title: task,
      body: `**Assignee:** ${assignee}\n**Source:** Stormee Bot\n\n*Generated automatically from meeting.*`,
      labels,
      assignees: ghUsername ? [ghUsername] : [],
    });
    console.log(`   -> Issue #${issue.data.number} created: "${task}"`);
  } catch (error) {
    console.error(`   -> Failed to create issue "${task}":`, error.message);
    throw error;
  }
}

export { processTranscript };