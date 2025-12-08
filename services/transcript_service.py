
import os
from datetime import datetime


class TranscriptService:
    """
    Service class for managing transcript file operations.
    Handles saving caption data as formatted text files with timestamps
    and managing their lifecycle (deletion).
    """

    def __init__(self, storage_dir="temp_transcripts"):
        """
        Initialize the TranscriptService with a storage directory.
        
        Args:
            storage_dir (str): Directory path where transcripts will be stored.
                             Defaults to "temp_transcripts".
        """
        self.storage_dir = storage_dir
        
        # Create storage directory if it doesn't exist
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

    def save_transcript(self, captions, meeting_id):
        """
        Save caption data as a formatted transcript file.
        
        Args:
            captions (list): List of caption entries, each containing 'timestamp' and 'text' keys.
            meeting_id (str): Unique identifier for the meeting.
        
        Returns:
            str: Full file path of the saved transcript, or None if captions list is empty.
        """
        # Return None if captions list is empty
        if not captions:
            return None
        
        # Accumulate formatted transcript lines
        transcript_content = []
        
        # Format each caption entry with timestamp
        for entry in captions:
            timestamp = entry.get('timestamp', '00:00:00')
            text = entry.get('text', '')
            formatted_line = f"[{timestamp}] {text}"
            transcript_content.append(formatted_line)
        
        # Join all lines with newline characters
        formatted_transcript = "\n".join(transcript_content)
        
        # Generate unique filename with current timestamp
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transcript_{meeting_id}_{timestamp_str}.txt"
        
        # Construct full file path
        file_path = os.path.join(self.storage_dir, filename)
        
        # Write transcript to file with error handling
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(formatted_transcript)
            return file_path
        except IOError as e:
            print(f"Error writing transcript file: {e}")
            raise

    def delete_transcript(self, file_path):
        """
        Delete a transcript file from storage.
        
        Args:
            file_path (str): Full path to the transcript file to delete.
        """
        # Check if file_path is not None and file exists
        if file_path is not None and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Transcript file deleted successfully: {file_path}")
            except OSError as e:
                print(f"Error deleting transcript file: {e}")
        else:
            print(f"Transcript file not found: {file_path}")

import os
from datetime import datetime


class TranscriptService:
    """
    Service class for managing transcript file operations.
    Handles saving caption data as formatted text files with timestamps
    and managing their lifecycle (deletion).
    """

    def __init__(self, storage_dir="temp_transcripts"):
        """
        Initialize the TranscriptService with a storage directory.
        
        Args:
            storage_dir (str): Directory path where transcripts will be stored.
                             Defaults to "temp_transcripts".
        """
        self.storage_dir = storage_dir
        
        # Create storage directory if it doesn't exist
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

    def save_transcript(self, captions, meeting_id):
        """
        Save caption data as a formatted transcript file.
        
        Args:
            captions (list): List of caption entries, each containing 'timestamp' and 'text' keys.
            meeting_id (str): Unique identifier for the meeting.
        
        Returns:
            str: Full file path of the saved transcript, or None if captions list is empty.
        """
        # Return None if captions list is empty
        if not captions:
            return None
        
        # Accumulate formatted transcript lines
        transcript_content = []
        
        # Format each caption entry with timestamp
        for entry in captions:
            timestamp = entry.get('timestamp', '00:00:00')
            text = entry.get('text', '')
            formatted_line = f"[{timestamp}] {text}"
            transcript_content.append(formatted_line)
        
        # Join all lines with newline characters
        formatted_transcript = "\n".join(transcript_content)
        
        # Generate unique filename with current timestamp
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transcript_{meeting_id}_{timestamp_str}.txt"
        
        # Construct full file path
        file_path = os.path.join(self.storage_dir, filename)
        
        # Write transcript to file with error handling
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(formatted_transcript)
            return file_path
        except IOError as e:
            print(f"Error writing transcript file: {e}")
            raise

    def delete_transcript(self, file_path):
        """
        Delete a transcript file from storage.
        
        Args:
            file_path (str): Full path to the transcript file to delete.
        """
        # Check if file_path is not None and file exists
        if file_path is not None and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Transcript file deleted successfully: {file_path}")
            except OSError as e:
                print(f"Error deleting transcript file: {e}")
        else:
            print(f"Transcript file not found: {file_path}")