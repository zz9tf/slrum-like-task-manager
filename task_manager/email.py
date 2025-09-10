#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Notification Module
"""

import json
import base64
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail API imports
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False


class EmailNotifier:
    """Email Notifier"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load email configuration"""
        # Only use email_config.json
        email_config_file = self.data_dir / "config" / "email_config.json"
        token_file = self.data_dir / "config" / "token.json"
        
        if email_config_file.exists():
            try:
                with open(email_config_file, 'r', encoding='utf-8') as f:
                    email_config = json.load(f)
                    return {
                        "enabled": email_config.get("enabled", False),
                        "to_email": email_config.get("to_email", ""),
                        "token_file": str(token_file)
                    }
            except Exception as e:
                print(f"⚠️ Failed to load email config: {e}")
        
        # Default config
        return {
            "enabled": False,
            "to_email": "",
            "token_file": str(token_file)
        }
    
    def _get_gmail_credentials(self):
        """Get Gmail API credentials"""
        if not GMAIL_API_AVAILABLE:
            print("❌ Gmail API library not available")
            return None
        
        token_file = Path(self.config['token_file'])
        if not token_file.exists():
            print("❌ Token file not found")
            return None
        
        try:
            creds = Credentials.from_authorized_user_file(str(token_file))
            
            # Refresh token if needed
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Save refreshed token
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            
            return creds
        except Exception as e:
            print(f"❌ Failed to load credentials: {e}")
            return None
    
    def _send_email(self, subject: str, body: str) -> bool:
        """Send email using Gmail API"""
        if not self.config.get('enabled', False):
            print("❌ Email notifications not enabled")
            return False
        
        if not self.config.get('to_email'):
            print("❌ No recipient email configured")
            return False
        
        creds = self._get_gmail_credentials()
        if not creds:
            return False
        
        try:
            service = build('gmail', 'v1', credentials=creds)
            
            # Create message
            message = MIMEMultipart()
            message['to'] = self.config['to_email']
            message['subject'] = subject
            
            message.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send message
            send_message = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            print(f"📧 Email sent successfully: {send_message['id']}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    def send_task_completion_email(self, task):
        """Send task completion email"""
        if not self.config.get('enabled', False):
            return
        
        status_icons = {
            'completed': '✅',
            'failed': '❌',
            'killed': '🛑'
        }
        
        status_icon = status_icons.get(task.status, '❓')
        
        subject = f"Task {task.id} - {task.name} {status_icon} {task.status.title()}"
        
        # Calculate duration
        duration = "N/A"
        if task.start_time and task.end_time:
            duration = str(task.end_time - task.start_time).split('.')[0]
        elif task.start_time:
            from datetime import datetime
            duration = str(datetime.now() - task.start_time).split('.')[0] + "s"
        
        body = f"""Task Management System Notification

Task Details:
- ID: {task.id}
- Name: {task.name}
- Status: {status_icon} {task.status.title()}
- Priority: {task.priority}
- Duration: {duration}
- Created: {task.created_time}
- Started: {task.start_time or 'N/A'}
- Ended: {task.end_time or 'N/A'}
- Command: {task.command}

Task completed at {task.end_time or 'Unknown time'}.

---
Task Management System
"""
        
        if task.error_message:
            body += f"\nError: {task.error_message}"
        
        self._send_email(subject, body)
    
    def test_email(self) -> bool:
        """Send test email"""
        subject = "Task Management System - Test Email"
        body = """This is a test email from the Task Management System.

If you receive this email, the email notification system is working correctly.

---
Task Management System
"""
        return self._send_email(subject, body)
