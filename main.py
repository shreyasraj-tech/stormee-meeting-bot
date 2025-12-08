
import asyncio
import logging
from aiohttp import web
from python_socketio import AsyncServer
from services.stormee_meet_bot_service import MeetBot
from services.transcript_service import TranscriptService
from services.email_service import EmailService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize SocketIO server
sio = AsyncServer(
    async_mode='aiohttp',
    cors_allowed_origins='*',
    ping_timeout=60,
    ping_interval=25
)

# Initialize aiohttp app
app = web.Application()
sio.attach(app)

# Dictionary to track bot instances per session
bots = {}


@sio.event
async def connect(sid, environ):
    """
    Handle client connection event.
    Creates a new MeetBot instance for the session.
    
    Args:
        sid (str): Session ID
        environ (dict): Environment dictionary containing HTTP headers
    """
    logger.info(f"Client connected: {sid}")
    
    # Extract meet_url and user_email from HTTP headers
    meet_url = environ.get('HTTP_MEET_URL', 'http://example.com')
    user_email = environ.get('HTTP_USER_EMAIL', 'user@example.com')
    
    # Create a new MeetBot instance for this session
    bot = MeetBot(meet_url, user_email)
    
    # Store the bot instance in the bots dictionary
    bots[sid] = bot
    
    logger.info(f"MeetBot instance created for session {sid}")


@sio.event
async def disconnect(sid):
    """
    Handle client disconnection event.
    Cleans up the bot instance for the session.
    
    Args:
        sid (str): Session ID
    """
    logger.info(f"Client disconnected: {sid}")
    
    # Check if the bot instance exists for this session
    if sid in bots:
        bot = bots[sid]
        
        # Gracefully shut down the bot if it exists
        if bot is not None:
            try:
                await bot.stop()
                logger.info(f"Bot stopped for session {sid}")
            except Exception as e:
                logger.error(f"Error stopping bot for session {sid}: {e}")
        
        # Remove the bot instance from the dictionary
        del bots[sid]
        logger.info(f"Bot instance removed for session {sid}")


@sio.event
async def callEnded(sid, data):
    """
    Handle the callEnded event.
    Orchestrates the post-meeting workflow: retrieve captions, save transcript,
    send email, and perform cleanup.
    
    Args:
        sid (str): Session ID
        data (dict): Event data containing meeting information
    """
    print(f"Call ended for session {sid} with data: {data}")
    
    # Check if the bot instance exists for this session
    if sid not in bots:
        print(f"No bot instance found for session {sid}")
        return
    
    # Retrieve the bot instance
    bot = bots[sid]
    
    # Get the accumulated captions from the bot
    captions = bot.get_captions()
    
    # Retrieve the user email from the bot
    user_email = bot.user_email
    
    # Check if captions list is empty
    if not captions:
        print(f"No captions captured for session {sid}")
        try:
            await bot.stop()
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
        
        # Clean up the bot instance
        if sid in bots:
            del bots[sid]
        return
    
    # Create service instances
    transcript_service = TranscriptService()
    email_service = EmailService()
    
    # Initialize file_path to track the transcript file location
    file_path = None
    
    try:
        # Extract meeting_id from data, use sid as fallback
        meeting_id = data.get('meetingId', sid)
        
        # Save the transcript
        file_path = transcript_service.save_transcript(captions, meeting_id)
        print(f"Transcript saved for meeting {meeting_id} at {file_path}")
        
        # Send the transcript via email
        subject = f"Your Google Meet Transcript for meeting {meeting_id}"
        success = await email_service.send_transcript_email(user_email, file_path, subject)
        
        # If email was sent successfully, delete the transcript file
        if success:
            print(f"Transcript email sent successfully to {user_email}")
            transcript_service.delete_transcript(file_path)
        else:
            print(f"Failed to send transcript email. File retained at {file_path} for manual recovery.")
    
    except Exception as e:
        logger.error(f"Error in callEnded handler for session {sid}: {e}")
        if file_path is not None:
            print(f"Transcript file retained at {file_path} for manual recovery.")
    
    finally:
        # Ensure the bot is stopped
        try:
            await bot.stop()
            logger.info(f"Bot stopped for session {sid}")
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
        
        # Remove the bot instance from the dictionary
        if sid in bots:
            del bots[sid]
            logger.info(f"Bot instance removed for session {sid}")


@sio.event
async def audioChunk(sid, data):
    """
    Handle audio chunk events from the client.
    
    Args:
        sid (str): Session ID
        data (dict): Audio chunk data
    """
    logger.debug(f"Audio chunk received for session {sid}")


@sio.event
async def error(sid, data):
    """
    Handle error events from the client.
    
    Args:
        sid (str): Session ID
        data (dict): Error data
    """
    logger.error(f"Error event for session {sid}: {data}")


async def index(request):
    """
    Serve the index page.
    
    Args:
        request: HTTP request object
    
    Returns:
        HTTP response with HTML content
    """
    return web.Response(text="WebSocket server is running", content_type='text/plain')


if __name__ == '__main__':
    # Add route for index page
    app.router.add_get('/', index)
    
    # Start the server
    logger.info("Starting WebSocket server on http://localhost:8080")
    web.run_app(app, host='localhost', port=8080)

