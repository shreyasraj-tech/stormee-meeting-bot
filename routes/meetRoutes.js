import express from "express";
import { loginController, speakController, startAudioController, startCaptionsController, stopAudioController, stopCaptionsController, sendMessageController, endMeetingController, sendSummaryController, summarizeController } from "../controllers/meetController.js";
import { authMiddleware } from '../middleware/auth.js';

const router = express.Router();

// Health check route
const checkingHealth = (req, res) => {
    res.status(200).json({ status: "OK", message: "Service is running" });
};

// API routes
router.post("/start", startCaptionsController);
router.post("/stop", stopCaptionsController);
router.get('/health', checkingHealth);
router.post('/playaudio', startAudioController);
router.post('/signin', loginController);
router.post('/pauseaudio', stopAudioController);
router.post('/speak', speakController);
router.post('/end-meeting', endMeetingController);

/**
 * @route   POST /api/meet/send-summary
 * @desc    Send a summary to the specified recipient email
 * @access  Public
 */
router.post('/send-summary', sendSummaryController);

/**
 * @route   POST /api/meet/send-message
 * @desc    Send a message to the Google Meet chat
 * @access  Private (should be protected by auth middleware)
 */
router.post('/send-message', authMiddleware, sendMessageController);

/**
 * @route   POST /api/meet/summarize
 * @desc    Generate a summary from translated meeting text
 * @access  Public
 */
router.post('/summarize', summarizeController);

export default router;
