import { joinMeeting, pauseAudio, playAudio, speak, startCaptions, stopCaptions, sendMessage, getBrowser, startParticipantMonitoring, stopParticipantMonitoring, meetingTranscript, sendSummary } from "../services/meetBot.js";
import { getActiveMeetPage } from "../services/playwrightManager.js";
import { processTranscript } from "../services/TaskService.js";
import { getMeetingSummary } from "../services/ecgService.js";

let currentMeetingUrl = null;

const startCaptionsController = async (req, res) => {
  
  startCaptions()
    .then(() => console.log("Captions started"))
    .catch((err) => console.error(err));

  res.json({ message: "Captions started" });
};

const stopCaptionsController = async (req, res) => {
  try {
    const captions = await stopCaptions();
    // For a more robust solution, consider a job queue:
// await transcriptQueue.add('process-transcript', { captions });

// For a minimal improvement, ensure the error is tracked:
processTranscript(captions).catch(error => {
  console.error('Error processing transcript:', error);
  // TODO: Add monitoring/alerting here (e.g., Sentry, DataDog)
}); 
    res.json({ message: "Captions stopped", captions });
  } catch (err) {
    res.status(500).json({ error: "Failed to stop captions" });
  }
};
const loginController=async(req,res)=>{
    try {
        const { meetingUrl } = req.body;
        if (!meetingUrl) return res.status(400).json({ error: "meetingUrl is required" });
      
        currentMeetingUrl = meetingUrl;
        joinMeeting(meetingUrl)
          .then(() => {
            console.log("Joined meeting");
            // Start monitoring participant count and trigger endMeetingController when only 1 participant remains
            startParticipantMonitoring(endMeetingController);
          })
          .catch((err) => console.error(err));
          res.json({message:"Meeting joined"})
    }
    catch(err){
        res.status(500).json({ error: "Failed to join meeting" });
    }
}
const startAudioController=async(req,res)=>{
    try{
        await playAudio('/Users/deepanshgupta/Desktop/bot-poc/file_example_WAV_1MG.wav');

        res.json({message:"Audio played"});
    }
    catch(err){
        res.status(500).json({error:"Failed to play audio"});
    }
}
const stopAudioController=async(req,res)=>{
    try{
        await pauseAudio();
        res.json({message:"Audio paused"});

    }
    catch(err){
        res.status(500).json({error:"Failed to pause audio"});
    }
}
const speakController=async(req,res)=>{
    try{
        await speak(currentMeetingUrl,'/Users/deepanshgupta/Desktop/bot-poc/file_example_WAV_1MG.wav',8000);
        res.json({message:"Audio played"});
    }
    catch(err){
        res.status(500).json({error:"Failed to play audio"});
    }
}

const sendMessageController = async (req, res) => {
  // Destructure message from request body
  const { message } = req.body;

  // Validate input: check if message is provided, is a string, and is not empty
  if (!message || typeof message !== 'string' || message.trim() === '') {
    return res.status(400).json({ error: 'Message is required and must be a non-empty string.' });
  }

  try {
    // Retrieve the active Playwright page object
    const page = getActiveMeetPage();

    // Check if an active Google Meet session exists
    if (!page) {
      return res.status(503).json({ error: 'No active Google Meet session found.' });
    }

    // Call the service function to send the message
    await sendMessage(page, message.trim());

    // Send success response
    res.status(200).json({ success: true, message: 'Message sent successfully.' });
  } catch (error) {
    // Log error for debugging purposes
    console.error('Error in sendMessageController:', error);

    // Send error response with appropriate status code
    res.status(500).json({ error: error.message || 'An internal server error occurred.' });
  }
};

const endMeetingController = async (req, res) => {
  try {
    // Stop the participant monitoring interval
    stopParticipantMonitoring();

    // Stop captions and retrieve the meeting transcript
    const transcript = await stopCaptions();

    // Transform the transcript array into a formatted text string
    // Each transcript object contains speaker and text properties
    const transcriptText = transcript
      .map(item => `${item.speaker}: ${item.text}`)
      .join('\n');

    // Call the eCG.AI service to generate a summary from the transcript
    const summary = await getMeetingSummary(transcriptText);

    // Retrieve the recipient email address from the request body
    // This comes from the initial API request that started the bot session
    const { recipientEmail } = req.body;

    // Send the summary email to the recipient
    await sendSummary(recipientEmail, summary);

    // Get the browser instance
    const browser = getBrowser();

    // Close the browser instance if it exists
    if (browser) {
      await browser.close();
    }

    // Send success response
    res.status(200).json({ message: 'Meeting ended and summary sent.' });
  } catch (error) {
    // Log the error for debugging purposes
    console.error('Error in endMeetingController:', error);

    // Send error response with appropriate status code
    res.status(500).json({ error: 'Failed to end meeting.' });
  }
};

const sendSummaryController = async (req, res) => {
  try {
    // Extract recipientEmail and summaryJson from request body
    const { recipientEmail, summaryJson } = req.body;

    // Call the sendSummary service function with extracted parameters
    await sendSummary(recipientEmail, summaryJson);

    // Send success response with 200 status code
    res.status(200).json({ success: true, message: 'Summary sent successfully.' });
  } catch (error) {
    // Log the error for debugging purposes
    console.error('Error in sendSummaryController:', error);

    // Map validation errors to 400 status code, server errors to 500
    // Validation errors from sendSummary service include specific error messages
    const statusCode = error.message && (
      error.message.includes('Invalid recipient email') ||
      error.message.includes('Invalid summary data') ||
      error.message.includes('must be')
    ) ? 400 : 500;

    // Send error response with appropriate status code and error message
    res.status(statusCode).json({ error: error.message || 'Failed to send summary.' });
  }
};

const summarizeController = async (req, res) => {
  try {
    // Extract the translated meeting text from request body
    const { text } = req.body;

    // Validate that the text field is present and not empty
    if (!text || typeof text !== 'string' || text.trim() === '') {
      return res.status(400).json({ error: 'Text is required and must be a non-empty string.' });
    }

    // Call the summarization service with the validated text
    const summary = await getMeetingSummary(text.trim());

    // Send success response with the generated summary
    res.status(200).json({ success: true, message: 'Summary generated successfully.', summary });
  } catch (error) {
    // Log the error for debugging purposes
    console.error('Error in summarizeController:', error);

    // Send error response with appropriate status code
    res.status(500).json({ error: error.message || 'Failed to generate summary.' });
  }
};

export { startCaptionsController, stopCaptionsController ,startAudioController,loginController,stopAudioController,speakController,sendMessageController,endMeetingController,sendSummaryController,summarizeController};
