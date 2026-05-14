

import nodemailer from 'nodemailer';
import { convert as htmlToText } from 'html-to-text';
import fs from 'fs';
import dotenv from 'dotenv';

// Load environment variables from .env file
dotenv.config();

/**
 * Formats meeting summary data into HTML email content.
 * This helper function takes a summary object and converts it into a properly formatted HTML email.
 * 
 * @param {Object} summaryJson - An object containing summary data with 'summary' and 'action_items' properties
 * @returns {string} HTML formatted email content
 */
function formatEmail(summaryJson) {
  // Extract summary text, defaulting to 'No summary available.' if not present
  const summary = summaryJson.summary || 'No summary available.';
  
  // Extract action items array, defaulting to empty array if not present
  const actionItems = summaryJson.action_items || [];
  
  // Create HTML list for action items
  let actionItemsHtml = '<ul>';
  
  if (actionItems.length > 0) {
    // Iterate over each action item and wrap in <li> tags
    actionItems.forEach(item => {
      actionItemsHtml += `<li>${item}</li>`;
    });
  } else {
    // Add default message if no action items identified
    actionItemsHtml += '<li>No action items identified.</li>';
  }
  
  actionItemsHtml += '</ul>';
  
  // Return complete HTML email content
  const htmlContent = `
    <h1>Meeting Summary</h1>
    <h2>Summary</h2>
    <p>${summary}</p>
    <h2>Action Items</h2>
    ${actionItemsHtml}
  `;
  
  return htmlContent;
}

/**
 * Sends a meeting summary email to the specified recipient.
 * This function formats the summary into HTML and plain text, configures email authentication,
 * and sends the email using Nodemailer.
 * 
 * @param {string} recipientEmail - The email address of the recipient
 * @param {Object} summaryJson - An object containing summary data with 'summary' and 'action_items' properties
 * @returns {Promise<void>}
 * @throws {Error} If email sending fails
 */
async function sendSummary(recipientEmail, summaryJson) {
  // Get HTML content from formatEmail helper function
  const htmlContent = formatEmail(summaryJson);
  
  // Convert HTML to plain text
  const textContent = htmlToText(htmlContent);
  
  // Declare transporter variable
  let transporter;
  
  // Check if auth.json file exists for OAuth2 authentication
  if (fs.existsSync('auth.json')) {
    // Read and parse auth.json file
    const auth = JSON.parse(fs.readFileSync('auth.json', 'utf-8'));
    
    // Create transporter with OAuth2 authentication
    transporter = nodemailer.createTransport({
      service: 'gmail',
      auth: {
        type: 'OAuth2',
        user: process.env.EMAIL_USER,
        clientId: process.env.GOOGLE_CLIENT_ID,
        clientSecret: process.env.GOOGLE_CLIENT_SECRET,
        refreshToken: auth.refresh_token
      }
    });
  } else {
    // Create transporter with SMTP credentials
    transporter = nodemailer.createTransport({
      service: 'gmail',
      auth: {
        user: process.env.EMAIL_USER,
        pass: process.env.EMAIL_PASS
      }
    });
  }
  
  // Create mail options object
  const mailOptions = {
    from: process.env.EMAIL_USER,
    to: recipientEmail,
    subject: 'Your Meeting Summary from Stormee Bot',
    html: htmlContent,
    text: textContent
  };
  
  // Send email with error handling
  try {
    // Send the email
    await transporter.sendMail(mailOptions);
    
    // Log success message
    console.log('Summary email sent successfully.');
  } catch (error) {
    // Log error message
    console.error('Error sending summary email:', error);
    
    // Throw new error with user-friendly message
    throw new Error('Failed to send summary email.');
  }
}

// Export functions using ES6 named export syntax
export { sendSummary };

