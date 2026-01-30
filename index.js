// index.js
import dotenv from 'dotenv';
import { scrapeCaptions } from './captionScraper.js';
import { processTranscript } from './taskService.js';

dotenv.config();

async function main() {
  const meetingUrl = process.argv[2] || 'mock-url';

  try {
    console.log("--- Stormee Bot Starting ---");

    // 1. Get Content
    const transcriptText = await scrapeCaptions(meetingUrl);

    // 2. Process Content & Sync Tasks
    const result = await processTranscript(transcriptText);

    // 3. Final Output
    console.log("\n--- Meeting Summary ---");
    console.log(result.summary);
    console.log("-----------------------");

  } catch (error) {
    console.error("🔥 Fatal Error:", error);
  }
}

main();