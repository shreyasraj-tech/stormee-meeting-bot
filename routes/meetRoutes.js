import express from "express";
import { loginController, speakController, startAudioController, startCaptionsController, stopAudioController, stopCaptionsController, sendMessageController } from "../controllers/meetController.js";

import { authMiddleware } from '../middleware/auth.js'; // Assuming the middleware is in '../middleware/auth.js'
import { authMiddleware } from '../middleware/auth.js'; // Example path, please adjust
router.post('/send-message', authMiddleware, sendMessageController);
const router = express.Router();

// Health check route
const checkingHealth = (req, res) => {
    res.status(200).json({ status: "OK", message: "Service is running" });
}

// API routes
router.post("/start", startCaptionsController);
router.post("/stop", stopCaptionsController);
router.get('/health', checkingHealth); // Fixed typo
router.post('/playaudio', startAudioController);
router.post('/signin',loginController);
router.post('/pauseaudio',stopAudioController);
router.post('/speak',speakController);

/**
 * @route   POST /api/meet/send-message
 * @desc    Send a message to the Google Meet chat
 * @access  Private (should be protected by auth middleware)
 */

router.post('/send-message', authMiddleware, sendMessageController);

export default router;
