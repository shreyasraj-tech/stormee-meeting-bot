
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from services.stormee_meet_bot_service import meet_bot


async def get_participant_count_controller():
    """
    Retrieve the current participant count from the Google Meet meeting.
    
    This controller function checks if the bot is currently in a meeting,
    retrieves the participant count from the meeting, and returns it in a
    JSON response. If the bot is not in a meeting or an error occurs,
    appropriate HTTP exceptions are raised.
    
    Returns:
        JSONResponse: A response containing the participant count and a success message.
        
    Raises:
        HTTPException: With status code 400 if bot is not in a meeting.
        HTTPException: With status code 500 if an error occurs during retrieval.
    """
    try:
        # Check if the bot is currently in a meeting
        if not meet_bot.page:
            raise HTTPException(
                status_code=400,
                detail="Bot is not in a meeting. Cannot get participant count."
            )
        
        # Retrieve the current participant count from the service
        count = await meet_bot.get_participant_count()
        
        # Return the participant count in a JSON response
        return JSONResponse(
            status_code=200,
            content={
                "message": "Successfully retrieved participant count.",
                "participantCount": count
            }
        )
    
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception as err:
        # Log the error and raise a 500 exception
        print(f"Error getting participant count: {err}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get participant count."
        )


async def leave_meeting_controller():
    """
    Command the bot to gracefully leave the current Google Meet meeting.
    
    This controller function checks if the bot is currently in a meeting,
    commands it to leave, and returns a confirmation in a JSON response.
    If the bot is not in a meeting or an error occurs, appropriate HTTP
    exceptions are raised.
    
    Returns:
        JSONResponse: A response confirming the bot has left the meeting.
        
    Raises:
        HTTPException: With status code 400 if bot is not in a meeting.
        HTTPException: With status code 500 if an error occurs during the leave operation.
    """
    try:
        # Check if the bot is currently in a meeting
        if not meet_bot.page:
            raise HTTPException(
                status_code=400,
                detail="Bot is not currently in a meeting."
            )
        
        # Command the bot to leave the meeting
        await meet_bot.leave_meeting()
        
        # Return a confirmation message in a JSON response
        return JSONResponse(
            status_code=200,
            content={
                "message": "Bot has left the meeting."
            }
        )
    
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception as err:
        # Log the error and raise a 500 exception
        print(f"Error leaving meeting: {err}")
        raise HTTPException(
            status_code=500,
            detail="Failed to leave meeting."
        )


async def get_recording_status_controller():
    """
    Retrieve the current recording status.
    
    This is a placeholder function for the recording status feature.
    The actual implementation is not yet available.
    
    Returns:
        JSONResponse: A response indicating the feature is not yet implemented.
    """
    return JSONResponse(
        status_code=200,
        content={
            "message": "Recording status feature is not yet implemented."
        }
    )
