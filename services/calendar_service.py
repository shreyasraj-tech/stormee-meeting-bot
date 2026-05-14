
import asyncio
import os
import sqlite3
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import aiohttp
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as OAuth2Credentials
from google.auth.oauthlib.flow import Flow
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

logger = logging.getLogger(__name__)

# Database path for token storage
DB_PATH = Path("calendar_tokens.db")
SCOPES = ["https://www.googleapis.com/auth/calendar"]


class TokenManager:
    """Manages OAuth2 token storage and refresh with SQLite backend and encryption."""
    
    def __init__(self):
        """Initialize TokenManager with SQLite database and encryption."""
        self.db_path = DB_PATH
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        self._initialize_db()
        self.refresh_task: Optional[asyncio.Task] = None
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key from environment or file."""
        key_env = os.getenv("ENCRYPTION_KEY")
        if key_env:
            return key_env.encode()
        
        key_file = Path(".encryption_key")
        if key_file.exists():
            with open(key_file, "rb") as f:
                return f.read()
        
        # Generate new key
        key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(key)
        logger.info("Generated new encryption key")
        return key
    
    def _initialize_db(self):
        """Initialize SQLite database with oauth_tokens table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS oauth_tokens (
                user_id TEXT PRIMARY KEY,
                refresh_token TEXT NOT NULL,
                access_token TEXT NOT NULL,
                expiry_time REAL NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_state (
                resource_id TEXT PRIMARY KEY,
                expiration REAL NOT NULL,
                user_id TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    
    def _encrypt(self, data: str) -> str:
        """Encrypt data using Fernet."""
        return self.cipher.encrypt(data.encode()).decode()
    
    def _decrypt(self, encrypted_data: str) -> str:
        """Decrypt data using Fernet."""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def store_token(self, user_id: str, token_data: Dict[str, Any]) -> bool:
        """Store OAuth2 token in encrypted SQLite database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            encrypted_refresh = self._encrypt(token_data.get("refresh_token", ""))
            encrypted_access = self._encrypt(token_data.get("access_token", ""))
            expiry_time = token_data.get("expires_in", 3600) + datetime.now().timestamp()
            now = datetime.now().timestamp()
            
            cursor.execute("""
                INSERT OR REPLACE INTO oauth_tokens 
                (user_id, refresh_token, access_token, expiry_time, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, encrypted_refresh, encrypted_access, expiry_time, now, now))
            
            conn.commit()
            conn.close()
            logger.info(f"Token stored for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store token: {e}")
            return False
    
    def get_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve and decrypt token from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT refresh_token, access_token, expiry_time 
                FROM oauth_tokens WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return {
                "refresh_token": self._decrypt(row[0]),
                "access_token": self._decrypt(row[1]),
                "expiry_time": row[2]
            }
        except Exception as e:
            logger.error(f"Failed to retrieve token: {e}")
            return None
    
    async def refresh_access_token(self, user_id: str) -> bool:
        """Refresh access token using refresh token."""
        try:
            token_data = self.get_token(user_id)
            if not token_data:
                logger.warning(f"No token found for user {user_id}")
                return False
            
            client_id = os.getenv("GOOGLE_CLIENT_ID")
            client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "refresh_token": token_data["refresh_token"],
                        "grant_type": "refresh_token"
                    }
                ) as resp:
                    if resp.status == 200:
                        new_token = await resp.json()
                        new_token["refresh_token"] = token_data["refresh_token"]
                        self.store_token(user_id, new_token)
                        logger.info(f"Token refreshed for user {user_id}")
                        return True
                    else:
                        logger.error(f"Failed to refresh token: {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return False
    
    async def start_background_refresh(self, user_id: str):
        """Start background task to refresh token 5 minutes before expiry."""
        async def refresh_loop():
            while True:
                try:
                    token_data = self.get_token(user_id)
                    if token_data:
                        # Check if token expires within 5 minutes
                        time_until_expiry = token_data["expiry_time"] - datetime.now().timestamp()
                        if time_until_expiry < 300:  # 5 minutes
                            await self.refresh_access_token(user_id)
                    
                    # Check every 4 minutes
                    await asyncio.sleep(240)
                except Exception as e:
                    logger.error(f"Error in refresh loop: {e}")
                    await asyncio.sleep(240)
        
        self.refresh_task = asyncio.create_task(refresh_loop())
        logger.info(f"Background refresh task started for user {user_id}")
    
    def stop_background_refresh(self):
        """Stop background refresh task."""
        if self.refresh_task:
            self.refresh_task.cancel()
            logger.info("Background refresh task stopped")


class CalendarService:
    """Google Calendar integration service with OAuth2, conflict detection, and sync."""
    
    def __init__(self):
        """Initialize CalendarService with TokenManager."""
        self.token_manager = TokenManager()
        self.calendar_service = None
        self.current_user_id: Optional[str] = None
        self.webhook_check_task: Optional[asyncio.Task] = None
        self.last_webhook_notification: Dict[str, float] = {}
    
    async def initialize_oauth2(self, user_id: str, state: str) -> Dict[str, str]:
        """Initialize OAuth2 authentication flow."""
        try:
            client_id = os.getenv("GOOGLE_CLIENT_ID")
            client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
            redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/google/callback")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES,
                redirect_uri_mismatch=True
            )
            
            auth_uri, state = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                state=state
            )
            
            logger.info(f"OAuth2 flow initialized for user {user_id}")
            return {"auth_uri": auth_uri, "state": state}
        except Exception as e:
            logger.error(f"Failed to initialize OAuth2: {e}")
            raise
    
    async def handle_oauth2_callback(self, user_id: str, code: str, state: str) -> bool:
        """Handle OAuth2 callback and store token."""
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )
            
            flow.fetch_token(code=code)
            creds = flow.credentials
            
            token_data = {
                "access_token": creds.token,
                "refresh_token": creds.refresh_token,
                "expires_in": int(creds.expiry.timestamp() - datetime.now().timestamp())
            }
            
            self.token_manager.store_token(user_id, token_data)
            self.current_user_id = user_id
            
            # Start background refresh task
            await self.token_manager.start_background_refresh(user_id)
            
            logger.info(f"OAuth2 token stored for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to handle OAuth2 callback: {e}")
            return False
    
    async def _get_calendar_service(self, user_id: str):
        """Get authenticated Google Calendar service."""
        try:
            token_data = self.token_manager.get_token(user_id)
            if not token_data:
                raise ValueError(f"No token found for user {user_id}")
            
            creds = OAuth2Credentials(
                token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.getenv("GOOGLE_CLIENT_ID"),
                client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
            )
            
            service = build("calendar", "v3", credentials=creds)
            return service
        except Exception as e:
            logger.error(f"Failed to get calendar service: {e}")
            raise
    
    async def detect_conflicts(self, user_id: str, start_time: str, end_time: str) -> Optional[Dict[str, Any]]:
        """Detect conflicts with existing Busy events."""
        try:
            service = await self._get_calendar_service(user_id)
            
            events_result = service.events().list(
                calendarId="primary",
                timeMin=start_time,
                timeMax=end_time,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            
            events = events_result.get("items", [])
            
            for event in events:
                # Check if event is marked as Busy (opaque)
                if event.get("transparency") != "transparent":
                    return {
                        "conflicting_event_id": event.get("id"),
                        "title": event.get("summary"),
                        "start": event.get("start"),
                        "end": event.get("end")
                    }
            
            return None
        except Exception as e:
            logger.error(f"Error detecting conflicts: {e}")
            raise
    
    async def schedule_meeting(self, user_id: str, meeting_details: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a meeting with conflict detection and attendee notifications."""
        try:
            # Check for conflicts
            conflict = await self.detect_conflicts(
                user_id,
                meeting_details["start_time"],
                meeting_details["end_time"]
            )
            
            if conflict:
                return {
                    "status": "conflict",
                    "code": 409,
                    "message": "Meeting time conflicts with existing event",
                    "conflicting_event": conflict
                }
            
            service = await self._get_calendar_service(user_id)
            
            # Prepare event object
            event = {
                "summary": meeting_details.get("title", "Meeting"),
                "description": meeting_details.get("description", ""),
                "start": {
                    "dateTime": meeting_details["start_time"],
                    "timeZone": meeting_details.get("timezone", "UTC")
                },
                "end": {
                    "dateTime": meeting_details["end_time"],
                    "timeZone": meeting_details.get("timezone", "UTC")
                },
                "attendees": meeting_details.get("attendees", [])
            }
            
            # Create event with notifications
            created_event = service.events().insert(
                calendarId="primary",
                body=event,
                sendUpdates="all"
            ).execute()
            
            logger.info(f"Meeting scheduled: {created_event.get('id')}")
            
            return {
                "status": "success",
                "code": 201,
                "event_id": created_event.get("id"),
                "event_status": created_event.get("status"),
                "html_link": created_event.get("htmlLink")
            }
        except Exception as e:
            logger.error(f"Failed to schedule meeting: {e}")
            raise
    
    async def update_meeting(self, user_id: str, meeting_id: str, update_details: Dict[str, Any]) -> Dict[str, Any]:
        """Update meeting with conflict re-validation."""
        try:
            service = await self._get_calendar_service(user_id)
            
            # Get existing event
            existing_event = service.events().get(
                calendarId="primary",
                eventId=meeting_id
            ).execute()
            
            # Check for conflicts if time is being changed
            if "start_time" in update_details or "end_time" in update_details:
                start_time = update_details.get("start_time", existing_event["start"]["dateTime"])
                end_time = update_details.get("end_time", existing_event["end"]["dateTime"])
                
                conflict = await self.detect_conflicts(user_id, start_time, end_time)
                if conflict and conflict.get("conflicting_event_id") != meeting_id:
                    return {
                        "status": "conflict",
                        "code": 409,
                        "message": "Updated meeting time conflicts with existing event",
                        "conflicting_event": conflict
                    }
                
                existing_event["start"]["dateTime"] = start_time
                existing_event["end"]["dateTime"] = end_time
            
            # Merge update details
            if "title" in update_details:
                existing_event["summary"] = update_details["title"]
            if "description" in update_details:
                existing_event["description"] = update_details["description"]
            if "attendees" in update_details:
                existing_event["attendees"] = update_details["attendees"]
            
            # Update event with notifications
            updated_event = service.events().update(
                calendarId="primary",
                eventId=meeting_id,
                body=existing_event,
                sendUpdates="all"
            ).execute()
            
            logger.info(f"Meeting updated: {meeting_id}")
            
            return {
                "status": "success",
                "code": 200,
                "event_id": updated_event.get("id"),
                "event_status": updated_event.get("status")
            }
        except Exception as e:
            logger.error(f"Failed to update meeting: {e}")
            raise
    
    async def get_meeting(self, user_id: str, meeting_id: str) -> Dict[str, Any]:
        """Retrieve meeting details from Google Calendar API."""
        try:
            service = await self._get_calendar_service(user_id)
            
            event = service.events().get(
                calendarId="primary",
                eventId=meeting_id
            ).execute()
            
            return {
                "status": "success",
                "code": 200,
                "event": {
                    "id": event.get("id"),
                    "title": event.get("summary"),
                    "description": event.get("description"),
                    "start": event.get("start"),
                    "end": event.get("end"),
                    "attendees": event.get("attendees", []),
                    "status": event.get("status"),
                    "html_link": event.get("htmlLink")
                }
            }
        except Exception as e:
            logger.error(f"Failed to get meeting: {e}")
            raise
    
    async def initialize_sync(self, user_id: str) -> Dict[str, Any]:
        """Initialize webhook registration and fallback polling for incremental sync."""
        try:
            service = await self._get_calendar_service(user_id)
            
            # Register Watch request
            watch_body = {
                "id": str(uuid.uuid4()),
                "type": "web_hook",
                "address": os.getenv("WEBHOOK_URL", "https://example.com/webhook")
            }
            
            watch_response = service.events().watch(
                calendarId="primary",
                body=watch_body
            ).execute()
            
            resource_id = watch_response.get("resourceId")
            expiration = watch_response.get("expiration")
            
            # Store webhook metadata
            conn = sqlite3.connect(self.token_manager.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO sync_state 
                (resource_id, expiration, user_id, created_at)
                VALUES (?, ?, ?, ?)
            """, (resource_id, float(expiration) / 1000, user_id, datetime.now().timestamp()))
            conn.commit()
            conn.close()
            
            # Start webhook monitoring
            self.last_webhook_notification[resource_id] = datetime.now().timestamp()
            await self._start_webhook_monitor(resource_id, user_id)
            
            logger.info(f"Webhook registered for user {user_id}")
            
            return {
                "status": "success",
                "resource_id": resource_id,
                "expiration": expiration
            }
        except Exception as e:
            logger.error(f"Failed to initialize sync: {e}")
            raise
    
    async def _start_webhook_monitor(self, resource_id: str, user_id: str):
        """Monitor webhook and fallback to polling if needed."""
        async def monitor_loop():
            while True:
                try:
                    # Check if webhook has failed (no notification for 15+ minutes)
                    last_notification = self.last_webhook_notification.get(resource_id, datetime.now().timestamp())
                    time_since_notification = datetime.now().timestamp() - last_notification
                    
                    if time_since_notification > 900:  # 15 minutes
                        logger.warning(f"Webhook failed for {resource_id}, falling back to polling")
                        await self._fallback_polling(user_id)
                    
                    await asyncio.sleep(300)  # Check every 5 minutes
                except Exception as e:
                    logger.error(f"Error in webhook monitor: {e}")
                    await asyncio.sleep(300)
        
        self.webhook_check_task = asyncio.create_task(monitor_loop())
    
    async def _fallback_polling(self, user_id: str):
        """Fallback polling mechanism for incremental sync."""
        try:
            service = await self._get_calendar_service(user_id)
            
            # Query for changed events using syncToken
            events_result = service.events().list(
                calendarId="primary",
                syncToken=os.getenv("SYNC_TOKEN", ""),
                singleEvents=True
            ).execute()
            
            events = events_result.get("items", [])
            next_sync_token = events_result.get("nextSyncToken")
            
            logger.info(f"Polling sync retrieved {len(events)} changed events")
            
            # Store new sync token
            if next_sync_token:
                os.environ["SYNC_TOKEN"] = next_sync_token
            
            return {
                "status": "success",
                "events": events,
                "next_sync_token": next_sync_token
            }
        except Exception as e:
            logger.error(f"Fallback polling failed: {e}")
            raise
    
    def record_webhook_notification(self, resource_id: str):
        """Record webhook notification timestamp."""
        self.last_webhook_notification[resource_id] = datetime.now().timestamp()
        logger.debug(f"Webhook notification recorded for {resource_id}")
    
    async def cleanup(self):
        """Cleanup resources."""
        self.token_manager.stop_background_refresh()
        if self.webhook_check_task:
            self.webhook_check_task.cancel()
        logger.info("CalendarService cleanup completed")


# Module-level instance
_calendar_service: Optional[CalendarService] = None


def get_calendar_service() -> CalendarService:
    """Get or create CalendarService instance."""
    global _calendar_service
    if _calendar_service is None:
        _calendar_service = CalendarService()
    return _calendar_service

