
import axios from 'axios';
import dotenv from 'dotenv';

// Load environment variables from .env file
dotenv.config();

/**
 * Sends a meeting transcript to the eCG.AI API for summarization.
 * This function processes the transcript and returns a structured summary with action items.
 * 
 * @param {string} transcriptText - The meeting transcript text to be summarized
 * @returns {Promise<Object>} A summary object containing the summarized content and action items
 * @throws {Error} If the API key is not set or the API request fails
 */
async function getMeetingSummary(transcriptText) {
  // Retrieve the API key from environment variables
  const apiKey = process.env.ECG_API_KEY;
  
  // Validate that the API key is set
  if (!apiKey) {
    throw new Error('ECG_API_KEY is not set in the environment variables.');
  }
  
  try {
    // Construct the API request payload
    const payload = {
      model: 'ecg-default',
      prompt: 'Analyze the following transcript. Return a JSON object with \'summary\' and \'action_items\'.',
      text: transcriptText
    };
    
    // Make the POST request to the eCG.AI API
    const response = await axios.post(
      'https://api.ecg.ai/v1/summarize',
      payload,
      {
        headers: {
          'Authorization': 'Bearer ' + apiKey,
          'Content-Type': 'application/json'
        }
      }
    );
    
    // Return the API response data
    return response.data;
  } catch (error) {
    // Log the error for debugging purposes
    console.error('Error getting meeting summary from eCG.AI:', error);
    
    // Throw a new error with a user-friendly message
    throw new Error('Failed to get meeting summary.');
  }
}

// Export the function using ES6 named export syntax
export { getMeetingSummary };

