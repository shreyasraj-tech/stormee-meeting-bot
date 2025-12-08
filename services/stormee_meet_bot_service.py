
import asyncio
import logging
from datetime import datetime
from typing import Optional
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MeetBot:
    """
    Automates interactions with Google Meet using Playwright.
    Handles browser launching, authentication, joining meetings,
    and capturing captions with timestamps.
    """

    def __init__(self, meet_url, user_email=None):
        """
        Initialize the MeetBot instance.
        
        Args:
            meet_url (str): The URL of the Google Meet session.
            user_email (str, optional): Email for authentication. Defaults to None.
        """
        self.meet_url = meet_url
        self.user_email = user_email
        self.browser = None
        self.page = None
        self.context = None
        self.captions = []  # Store caption data during the meeting
        self.caption_task: Optional[asyncio.Task] = None
        self.participant_count = 0
        self.participant_task: Optional[asyncio.Task] = None
        logger.info(f"MeetBot initialized for meeting: {meet_url}")

    def capture_caption(self, text, timestamp):
        """
        Capture a caption with its timestamp and store it.
        
        Args:
            text (str): The caption text to capture.
            timestamp (str): The timestamp when the caption was captured.
        
        Returns:
            None
        """
        # Check if text is not empty (truthy check)
        if text:
            # Create a dictionary with timestamp and text
            caption_entry = {
                "timestamp": timestamp,
                "text": text
            }
            # Append to captions list
            self.captions.append(caption_entry)
            # Log the captured caption
            logger.info(f"Captured caption at {timestamp}: {text}")

    def get_captions(self):
        """
        Retrieve all captured captions.
        
        Returns:
            list: List of caption dictionaries with 'timestamp' and 'text' keys.
        """
        return self.captions

    async def get_participant_count(self) -> int:
        """
        Get the current participant count from the Google Meet UI.
        
        Attempts to scrape the participant count using two methods:
        1. Primary: Look for the participant count span element
        2. Fallback: Extract count from the "Show everyone" button aria-label
        
        Returns:
            int: The current participant count, or the last known count if retrieval fails.
        """
        if not self.page:
            return 0
        
        try:
            # Try primary selector for participant count
            try:
                element = await self.page.wait_for_selector('span[jsname="uVd3ic"]', timeout=5000)
                text_content = await element.text_content()
                if text_content:
                    count = int(text_content.strip())
                    return count
            except Exception:
                # Primary selector failed, try fallback
                pass
            
            # Fallback: Try to find the "Show everyone" button
            try:
                button = await self.page.query_selector('button[aria-label*="Show everyone"]')
                if button:
                    aria_label = await button.get_attribute('aria-label')
                    if aria_label:
                        # Parse number from text like "Show everyone (15)"
                        start_idx = aria_label.rfind('(')
                        end_idx = aria_label.rfind(')')
                        if start_idx != -1 and end_idx != -1:
                            count_str = aria_label[start_idx + 1:end_idx]
                            count = int(count_str)
                            return count
            except Exception:
                pass
            
            # If both methods fail, return the last known count
            logger.warning(f"Could not retrieve participant count, returning last known count: {self.participant_count}")
            return self.participant_count
        
        except Exception as e:
            logger.error(f"Error getting participant count: {e}")
            return self.participant_count

    async def _monitor_participants(self):
        """
        Background task to monitor participant count and detect bot removal.
        
        This method continuously monitors the participant count and checks if the
        bot is still in the meeting. If the "Leave call" button is no longer visible,
        it indicates the bot has been removed from the meeting.
        
        Returns:
            None
        """
        while True:
            try:
                # Check every 15 seconds
                await asyncio.sleep(15)
                
                # Get the current participant count
                current_count = await self.get_participant_count()
                
                # Compare with last known count and log if changed
                if current_count != self.participant_count:
                    logger.info(f"Participant count changed from {self.participant_count} to {current_count}")
                    self.participant_count = current_count
                
                # Check if the "Leave call" button is still visible
                if self.page and not self.page.is_closed():
                    leave_button = await self.page.query_selector('button[aria-label="Leave call"]')
                    if not leave_button:
                        # Bot may have been removed from the meeting
                        logger.info("Leave call button not found. Bot may have been removed from the meeting.")
                        await self.leave_meeting()
                        break
            
            except Exception as e:
                logger.error(f"Error in participant monitoring: {e}")
                break

    async def start_participant_monitoring(self):
        """
        Start the background participant monitoring task.
        
        This method creates and starts an asyncio task that monitors participant
        count and detects when the bot is removed from the meeting.
        
        Returns:
            None
        """
        # Check if monitoring is already active
        if self.participant_task and not self.participant_task.done():
            logger.info("Participant monitoring is already active")
            return
        
        # Create and start the monitoring task
        self.participant_task = asyncio.create_task(self._monitor_participants())
        logger.info("Participant monitoring started")

    async def leave_meeting(self):
        """
        Gracefully exit the meeting and clean up resources.
        
        This method cancels any running monitoring tasks, clicks the "Leave call" button,
        and closes the browser context and browser instance.
        
        Returns:
            None
        """
        if not self.page:
            logger.warning("Page is not available. Cannot leave meeting.")
            return
        
        try:
            # Cancel caption monitoring task if it exists and is running
            if self.caption_task and not self.caption_task.done():
                self.caption_task.cancel()
                logger.info("Caption monitoring task cancelled")
            
            # Cancel participant monitoring task if it exists and is running
            if self.participant_task and not self.participant_task.done():
                self.participant_task.cancel()
                logger.info("Participant monitoring task cancelled")
            
            # Locate and click the "Leave call" button
            leave_button = await self.page.query_selector('button[aria-label="Leave call"]')
            if leave_button:
                await leave_button.click()
                logger.info("Successfully clicked the Leave call button")
            else:
                logger.warning("Leave call button not found")
            
            # Close the browser context
            if self.context:
                await self.context.close()
                logger.info("Browser context closed")
            
            # Close the browser
            if self.browser:
                await self.browser.close()
                logger.info("Browser closed")
            
            # Set references to None
            self.page = None
            self.context = None
            self.browser = None
        
        except Exception as e:
            logger.error(f"Error leaving meeting: {e}")
            raise

    async def _monitor_captions(self):
        """
        Background task to monitor and scrape captions from the Google Meet page.
        
        This method continuously monitors the page for new captions and captures them
        with timestamps. It runs as a background task during the meeting.
        
        Returns:
            None
        """
        # Caption selector for Google Meet captions container
        caption_selector = 'div[data-is-captions-and-translations-container]'
        
        # Continue monitoring while page exists and is not closed
        while self.page and not self.page.is_closed():
            try:
                # Conceptual logic:
                # 1. Extract caption text from the page using the caption_selector
                # 2. Get the current timestamp
                # 3. Check if the language is English
                # 4. Call self.capture_caption(text, timestamp) to store the caption
                
                # Placeholder to prevent busy-waiting
                await asyncio.sleep(1)
                
            except Exception as e:
                # Log error and break out of the loop
                logger.error(f"Error monitoring captions: {e}")
                break

    async def start(self):
        """
        Start the MeetBot and initialize browser session.
        
        Returns:
            None
        """
        logger.info("Starting MeetBot...")
        # Placeholder for browser initialization logic
        pass

    async def stop(self):
        """
        Stop the MeetBot and clean up resources.
        
        Returns:
            None
        """
        logger.info("Stopping MeetBot...")
        # Placeholder for cleanup logic
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()


# Global MeetBot instance for use across the application
meet_bot = MeetBot(meet_url="", user_email=None)