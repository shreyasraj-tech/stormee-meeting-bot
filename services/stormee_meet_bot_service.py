
import asyncio
import os
import platform
import re
import logging
import time
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import socketio
from dotenv import load_dotenv
from html import unescape
import html

load_dotenv()

AUTH_PATH = Path("auth.json")
USERS_CONFIG_PATH = Path("users.yaml")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for input validation
MAX_TEXT_LENGTH = 100000
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'


class InputValidator:
    """Utility class for input validation and sanitization"""
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = MAX_TEXT_LENGTH) -> str:
        """
        Sanitize text by removing HTML entities and script tags.
        
        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
            
        Raises:
            ValueError: If text exceeds max_length
        """
        if not isinstance(text, str):
            raise ValueError("Input must be a string")
        
        if len(text) > max_length:
            raise ValueError(f"Text exceeds maximum length of {max_length} characters")
        
        # Remove script tags and their content
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove other potentially dangerous tags
        text = re.sub(r'<iframe[^>]*>.*?</iframe>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<object[^>]*>.*?</object>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<embed[^>]*>', '', text, flags=re.IGNORECASE)
        
        # Decode HTML entities
        text = unescape(text)
        
        return text.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format using regex pattern.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(email, str):
            return False
        return re.match(EMAIL_REGEX, email) is not None
    
    @staticmethod
    def validate_summary_json(summary_json: Dict) -> bool:
        """
        Validate summary JSON structure.
        
        Args:
            summary_json: Summary object to validate
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValueError: If required fields are missing or incorrectly typed
        """
        if not isinstance(summary_json, dict):
            raise ValueError("Summary must be a dictionary")
        
        required_fields = ['summary', 'action_items']
        for field in required_fields:
            if field not in summary_json:
                raise ValueError(f"Missing required field: {field}")
            
            if field == 'summary' and not isinstance(summary_json[field], str):
                raise ValueError(f"Field '{field}' must be a string")
            
            if field == 'action_items' and not isinstance(summary_json[field], list):
                raise ValueError(f"Field '{field}' must be a list")
        
        return True


class ConfigLoader:
    """Utility class for loading and managing configuration files"""
    
    def __init__(self, config_path: Path = USERS_CONFIG_PATH):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = config_path
        self.users_config: Dict = {}
        self.load_config()
    
    def load_config(self) -> Dict:
        """
        Load users configuration from YAML file with retry logic.
        
        Returns:
            Configuration dictionary
        """
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                if self.config_path.exists():
                    with open(self.config_path, 'r') as f:
                        self.users_config = yaml.safe_load(f) or {}
                    logger.info(f"✅ Loaded configuration from {self.config_path}")
                    return self.users_config
                else:
                    logger.warning(f"⚠️ Configuration file not found: {self.config_path}")
                    self.users_config = {}
                    return {}
            except Exception as e:
                logger.error(f"❌ Error loading config (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"Failed to load configuration after {max_retries} attempts")
                    self.users_config = {}
                    return {}
    
    def get_user_by_platform_id(self, platform_id: str) -> Optional[Dict]:
        """
        Get user profile by platform ID.
        
        Args:
            platform_id: Platform-specific user ID
            
        Returns:
            User profile dictionary or None
        """
        users = self.users_config.get('users', [])
        for user in users:
            if user.get('platform_id') == platform_id:
                return user
        return None
    
    def reload_config(self) -> Dict:
        """
        Reload configuration from file.
        
        Returns:
            Updated configuration dictionary
        """
        logger.info("🔄 Reloading configuration...")
        return self.load_config()
