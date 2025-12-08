
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


class EmailService:
    """
    Service class for sending emails with transcript attachments.
    Handles SMTP configuration from environment variables and provides
    robust error handling for email delivery operations.
    """

    def __init__(self):
        """
        Initialize the EmailService with SMTP configuration from environment variables.
        
        Configuration loaded from environment:
        - SMTP_SERVER: SMTP server address
        - SMTP_PORT: SMTP server port (default: 587)
        - SMTP_USER: SMTP authentication username
        - SMTP_PASSWORD: SMTP authentication password
        - SENDER_EMAIL: Email address to send from (falls back to SMTP_USER if not set)
        """
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.sender_email = os.getenv('SENDER_EMAIL', self.smtp_user)

    async def send_transcript_email(self, to_email, file_path, subject):
        """
        Send a transcript file via email with proper MIME formatting and error handling.
        
        Args:
            to_email (str): Recipient email address.
            file_path (str): Full path to the transcript file to attach.
            subject (str): Email subject line.
        
        Returns:
            bool: True if email sent successfully, False otherwise.
        """
        # Validate that all SMTP configuration values are present
        if not all([self.smtp_server, self.smtp_port, self.smtp_user, self.smtp_password]):
            print("Error: Missing SMTP configuration. Please set SMTP_SERVER, SMTP_PORT, SMTP_USER, and SMTP_PASSWORD environment variables.")
            return False

        # Create a multipart email message
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = to_email
        msg['Subject'] = subject

        # Create and attach the email body
        body = "Please find the transcript of your recent Google Meet session attached."
        msg.attach(MIMEText(body, 'plain'))

        # Attach the transcript file
        try:
            with open(file_path, 'rb') as attachment:
                # Create a MIME base object for the file
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                
                # Encode the payload in base64
                encoders.encode_base64(part)
                
                # Add Content-Disposition header with filename
                part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(file_path)}')
                
                # Attach the file to the message
                msg.attach(part)
        except FileNotFoundError:
            print(f"Error: Transcript file not found at {file_path}")
            return False

        # Send the email via SMTP
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            print(f"Transcript email sent successfully to {to_email}")
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


class EmailService:
    """
    Service class for sending emails with transcript attachments.
    Handles SMTP configuration from environment variables and provides
    robust error handling for email delivery operations.
    """

    def __init__(self):
        """
        Initialize the EmailService with SMTP configuration from environment variables.
        
        Configuration loaded from environment:
        - SMTP_SERVER: SMTP server address
        - SMTP_PORT: SMTP server port (default: 587)
        - SMTP_USER: SMTP authentication username
        - SMTP_PASSWORD: SMTP authentication password
        - SENDER_EMAIL: Email address to send from (falls back to SMTP_USER if not set)
        """
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.sender_email = os.getenv('SENDER_EMAIL', self.smtp_user)

    async def send_transcript_email(self, to_email, file_path, subject):
        """
        Send a transcript file via email with proper MIME formatting and error handling.
        
        Args:
            to_email (str): Recipient email address.
            file_path (str): Full path to the transcript file to attach.
            subject (str): Email subject line.
        
        Returns:
            bool: True if email sent successfully, False otherwise.
        """
        # Validate that all SMTP configuration values are present
        if not all([self.smtp_server, self.smtp_port, self.smtp_user, self.smtp_password]):
            print("Error: Missing SMTP configuration. Please set SMTP_SERVER, SMTP_PORT, SMTP_USER, and SMTP_PASSWORD environment variables.")
            return False

        # Create a multipart email message
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = to_email
        msg['Subject'] = subject

        # Create and attach the email body
        body = "Please find the transcript of your recent Google Meet session attached."
        msg.attach(MIMEText(body, 'plain'))

        # Attach the transcript file
        try:
            with open(file_path, 'rb') as attachment:
                # Create a MIME base object for the file
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                
                # Encode the payload in base64
                encoders.encode_base64(part)
                
                # Add Content-Disposition header with filename
                part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(file_path)}')
                
                # Attach the file to the message
                msg.attach(part)
        except FileNotFoundError:
            print(f"Error: Transcript file not found at {file_path}")
            return False

        # Send the email via SMTP
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            print(f"Transcript email sent successfully to {to_email}")
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False