
import { OpenAI } from 'openai';
import { Octokit } from 'octokit';

// Initialize API clients with environment variables
const openaiClient = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const octokitClient = new Octokit({
  auth: process.env.GITHUB_TOKEN,
});

/**
 * Process meeting transcript using OpenAI LLM
 * Extracts summary and action items from captions
 * @param {Array} captions - Array of caption objects with speaker and text properties
 * @returns {Promise<Object>} - Object containing summary and actionItems
 */
async function processTranscript(captions) {
  try {
    // Format captions into a single string
    const transcriptText = captions
      .map((caption) => `${caption.speaker}: ${caption.text}`)
      .join('\n');

    // Create prompt for LLM to analyze transcript
    const prompt = `Analyze the following meeting transcript and extract a summary and action items. Return a JSON object with two properties:
1. "summary": A brief summary of the meeting (2-3 sentences)
2. "actionItems": An array of action items, each with properties: "task" (description of the task), "assignee" (person responsible), "priority" (high/medium/low), and "type" (bug/feature/documentation/other)

Meeting Transcript:
${transcriptText}

Return ONLY valid JSON, no additional text.`;

    // Call OpenAI API
    const response = await openaiClient.chat.completions.create({
      model: process.env.LLM_MODEL || 'gpt-4o',
      messages: [
        {
          role: 'user',
          content: prompt,
        },
      ],
    });

    // Extract response text
    const responseText = response.choices[0].message.content;

    // Parse JSON response
    const parsedResponse = JSON.parse(responseText);

    // Validate that actionItems array exists
    if (!Array.isArray(parsedResponse.actionItems)) {
      throw new Error('Invalid response format: actionItems must be an array');
    }

    // Create GitHub issues for each action item
    for (const actionItem of parsedResponse.actionItems) {
      await createGitHubIssue(
        actionItem.task,
        actionItem.assignee,
        actionItem.priority,
        actionItem.type
      );
    }

    console.log('✅ Transcript processed successfully');
    return parsedResponse;
  } catch (error) {
    if (error instanceof SyntaxError) {
      console.error('❌ Error parsing LLM response:', error.message);
    } else if (error.message.includes('API')) {
      console.error('❌ Error processing transcript with LLM:', error.message);
    } else {
      console.error('❌ Error processing transcript:', error.message);
    }
    throw error;
  }
}

/**
 * Create a GitHub issue for an action item
 * @param {string} task - Task description
 * @param {string} assignee - Person responsible for the task
 * @param {string} priority - Priority level (high/medium/low)
 * @param {string} type - Issue type (bug/feature/documentation/other)
 * @returns {Promise<void>}
 */
async function createGitHubIssue(task, assignee, priority, type) {
  try {
    // Extract repository owner and name from environment variable
    const repoPath = process.env.GITHUB_REPO;
    if (!repoPath) {
      throw new Error('GITHUB_REPO environment variable is not set');
    }

    const [owner, repo] = repoPath.split('/');
    if (!owner || !repo) {
      throw new Error('GITHUB_REPO must be in format: owner/repo');
    }

    // Map priority and type to GitHub labels
    const priorityLabel = `priority-${priority?.toLowerCase() || 'medium'}`;
    const typeLabel = mapTypeToLabel(type);
    const labels = [priorityLabel, typeLabel].filter(Boolean);

    // Create GitHub issue
    const issue = await octokitClient.rest.issues.create({
      owner,
      repo,
      title: task,
      labels,
      assignees: assignee && assignee.trim() ? [assignee.trim()] : [],
    });

    console.log(`✅ GitHub issue created: #${issue.data.number} - ${task}`);
  } catch (error) {
    console.error('❌ Error creating GitHub issue:', error.message);
    throw error;
  }
}

/**
 * Map issue type to GitHub label
 * @param {string} type - Issue type
 * @returns {string} - GitHub label
 */
function mapTypeToLabel(type) {
  const typeMap = {
    bug: 'bug',
    feature: 'feature',
    documentation: 'documentation',
    other: 'task',
  };
  return typeMap[type?.toLowerCase()] || 'task';
}

export { processTranscript, createGitHubIssue };

