import { chromium } from 'playwright';

/**
 * Scrapes captions from a live Google Meet session.
 * 
 * Flow:
 * 1. Launches Browser (Headless: false to avoid bot detection).
 * 2. Joins the meeting as a Guest ("TaskSync Bot").
 * 3. Waits to be admitted by the host.
 * 4. Enables Captions (CC).
 * 5. Records caption text for a set duration.
 * 
 * @param {string} meetingUrl - The URL (e.g., https://meet.google.com/abc-defg-hij)
 * @returns {Promise<string>} The extracted caption text
 */
async function scrapeCaptions(meetingUrl) {
  console.log(`🎥 Launching TaskSync Bot for: ${meetingUrl}`);
  
  // 1. Launch Browser
  // We use headless: false because Google Meet often blocks headless browsers
  const browser = await chromium.launch({ 
    headless: false, 
    args: ['--use-fake-ui-for-media-stream', '--disable-blink-features=AutomationControlled'] 
  });

  const context = await browser.newContext({
    permissions: ['microphone', 'camera'], // Automatically grant mic/cam permissions
  });

  const page = await context.newPage();
  let allCaptions = [];

  try {
    // 2. Navigate to Meeting
    await page.goto(meetingUrl);

    // --- STEP: Handle Guest Login ---
    // Wait for the name input field (Guest mode)
    try {
      const nameInput = await page.waitForSelector('input[type="text"], input[placeholder="Your name"]', { timeout: 8000 });
      if (nameInput) {
        console.log("✍️ Entering Bot Name...");
        await nameInput.fill("TaskSync Bot");
        await page.keyboard.press('Enter');
      }
    } catch (e) {
      console.log("ℹ️ Name input not found (might be already logged in or different flow). Proceeding...");
    }

    // --- STEP: Click Join Button ---
    // Look for "Ask to join" or "Join now" buttons
    try {
      const joinButton = await page.getByRole('button', { name: /ask to join|join now/i }).first();
      await joinButton.click();
      console.log("👉 Clicked Join/Ask to Join");
    } catch (e) {
      console.error("❌ Could not find a 'Join' button. Checking if we are already in...");
    }

    // --- STEP: Wait for Admittance ---
    console.log("⏳ Waiting to be admitted by host... (Please click 'Admit' in the meeting window)");
    // We assume we are "in" when the 'Leave call' button appears
    await page.waitForSelector('button[aria-label="Leave call"]', { timeout: 120000 }); // 2 minute timeout for admittance
    console.log("✅ Successfully entered the meeting!");

    // --- STEP: Enable Captions ---
    try {
      // Try to find the CC button by aria-label
      const ccButton = await page.locator('button[aria-label="Turn on captions"], button[aria-label="Turn on closed captions"]');
      if (await ccButton.isVisible()) {
        await ccButton.click();
        console.log("cc Captions enabled.");
      } else {
        // Sometimes it's inside the "More options" menu
        console.log("⚠️ CC button visible not found directly. Attempting menu...");
        // (Simplified for this version: assuming standard CC button is present)
      }
    } catch (error) {
      console.log("⚠️ Could not toggle captions (might already be on).");
    }

    // --- STEP: Scrape Text ---
    console.log("🎙️ Listening for conversation...");
    
    // Scrape Duration: How long the bot stays in the meeting (e.g., 30 seconds for testing)
    const LISTEN_TIME_MS = 30000; 

    // We use page.evaluate to run code INSIDE the browser to watch for text changes
    allCaptions = await page.evaluate(async (duration) => {
      return new Promise((resolve) => {
        const capturedLines = new Set();
        const startTime = Date.now();

        // Observer looks for changes in the DOM body (where captions are injected)
        const observer = new MutationObserver((mutations) => {
          // Google Meet captions usually have a specific controller class or container
          // Robust approach: Look for the caption container or text updates at bottom of screen
          // Specific selector for Meet captions (subject to change by Google):
          const captionNodes = document.querySelectorAll('.iTTPOb, .VbkSUe, div[jscontroller="D1tHWc"]'); 
          
          captionNodes.forEach(node => {
            if (node.innerText && node.innerText.length > 0) {
              capturedLines.add(node.innerText);
            }
          });
        });

        observer.observe(document.body, { childList: true, subtree: true });

        // Stop listening after fixed duration
        setTimeout(() => {
          observer.disconnect();
          resolve(Array.from(capturedLines));
        }, duration);
      });
    }, LISTEN_TIME_MS);

    console.log("🛑 Scraping session finished.");

  } catch (error) {
    console.error("❌ Error during scraping:", error);
    throw new Error('Caption scraping failed during browser automation.');
  } finally {
    await browser.close();
  }

  // Join the array of lines into a single transcript string
  const finalTranscript = allCaptions.join('\n');
  
  if (!finalTranscript.trim()) {
    console.warn("⚠️ Warning: No captions were captured. Ensure someone was speaking and captions were enabled.");
    // Return a minimal fallback or empty string based on your error handling preference
    return "Meeting started but no audio content was transcribed.";
  }

  return finalTranscript;
}

export { scrapeCaptions };