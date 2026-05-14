import OpenAI from 'openai';
import dotenv from 'dotenv';

dotenv.config();

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const SYSTEM_PROMPT = `
You are "TaskSync", an intelligent meeting assistant.
Your goal is to analyze meeting transcripts and output structured data.

INSTRUCTIONS:
1. Summarize the meeting briefly.
2. Extract actionable tasks.
3. You must output VALID JSON only. No markdown formatting.

JSON STRUCTURE:
{
  "summary": "String summary...",
  "action_items": [
    {
      "task": "Title of the task",
      "assignee": "Name of person (or 'Unassigned')",
      "priority": "High | Medium | Low",
      "type": "Bug | Feature | Docs | Task"
    }
  ]
}
`;

/**
 * Sends transcript to LLM and returns structured JSON.
 * @param {string} transcript 
 * @returns {Promise<Object>} The parsed JSON result
 */
export async function analyzeMeetingContent(transcript) {
  try {
    console.log('🤖 TaskSync: Sending transcript to LLM...');
    
    const response = await openai.chat.completions.create({
      model: 'gpt-4-turbo', // or gpt-3.5-turbo-0125
      response_format: { type: 'json_object' }, // Enforces strict JSON
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: `Here is the meeting transcript:\n\n${transcript}` }
      ],
      temperature: 0.2, // Low temp for consistent data extraction
    });

    const content = response.choices[0].message.content;
    const parsedData = JSON.parse(content);
    
    console.log('✅ TaskSync: Analysis complete.');
    return parsedData;

  } catch (error) {
    console.error('❌ TaskSync LLM Error:', error);
    // Return empty structure to prevent crashes
    return { summary: "Analysis failed", action_items: [] };
  }
}