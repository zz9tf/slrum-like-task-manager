#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email notification module
"""

import json
import base64
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Gmail API imports
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False


class EmailNotifier:
    """Email notifier for sending task-related emails via Gmail API"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        # Prepare log file early so that _load_config and other methods can log
        logs_dir = self.data_dir / "logs"
        try:
            logs_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # Silently ignore log directory creation errors; do not block runtime
            pass
        self.log_file = logs_dir / "email.log"
        self.config = self._load_config()

    def _write_log(self, message: str) -> None:
        """Append a timestamped line to the email log file.

        This function should never raise to callers; any IOError is swallowed.
        """
        timestamp = datetime.utcnow().isoformat(timespec='seconds') + "Z"
        line = f"[{timestamp}] {message}\n"
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            # Do not let logging failures break primary flow
            pass
    
    def _load_config(self) -> dict:
        """Load email configuration"""
        config_file = self.data_dir / "config" / "email_config.json"
        token_file = self.data_dir / "config" / "token.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self._write_log("Loaded email_config.json successfully")
                    return {
                        "enabled": config.get("enabled", False),
                        "to_email": config.get("to_email", ""),
                        "token_file": str(token_file)
                    }
            except Exception as e:
                print(f"⚠️ Failed to load email configuration: {e}")
                self._write_log(f"WARN Failed to load email configuration: {e}")
        
        # Default config
        self._write_log("email_config.json not found; email notifications disabled by default")
        return {
            "enabled": False,
            "to_email": "",
            "token_file": str(token_file)
        }
    
    def _get_gmail_credentials(self):
        """Obtain Gmail API credentials, refreshing token if expired"""
        if not GMAIL_API_AVAILABLE:
            print("❌ Gmail API libraries are not available")
            self._write_log("ERROR Gmail API libraries not available")
            return None
        
        SCOPES = ['https://www.googleapis.com/auth/gmail.send']
        creds = None
        token_file = self.config.get("token_file")
        
        if not token_file or not Path(token_file).exists():
            print(f"❌ Token file not found: {token_file}")
            self._write_log(f"ERROR Token file not found: {token_file}")
            return None
        
        try:
            # Load existing token
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            
            # If token invalid, attempt refresh
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    print("🔄 Refreshing expired token...")
                    self._write_log("INFO Token expired, attempting refresh")
                    creds.refresh(Request())
                    # Persist refreshed credentials
                    with open(token_file, 'w') as token:
                        token.write(creds.to_json())
                    print("✅ Token refresh succeeded")
                    self._write_log("INFO Token refresh succeeded; token persisted")
                else:
                    print("❌ No valid credentials; please login again")
                    self._write_log("ERROR No valid credentials; login required (missing/invalid refresh token)")
                    return None
            
            # Log current credential status
            try:
                expiry_str = getattr(creds, 'expiry', None)
                self._write_log(f"INFO Credentials ready; expiry={expiry_str}")
            except Exception:
                pass

            return creds
            
        except Exception as e:
            print(f"❌ Failed to load Gmail credentials: {e}")
            self._write_log(f"ERROR Failed to load Gmail credentials: {e}")
            return None
    
    def send_email(self, subject: str, body: str, task_id: str = None) -> bool:
        """Send an email notification via Gmail API"""
        if not self.config.get("enabled", False):
            self._write_log("INFO Email send skipped: notifications disabled")
            return False
        
        if not GMAIL_API_AVAILABLE:
            print("❌ Gmail API libraries are not available")
            self._write_log("ERROR Email send failed: Gmail API libraries not available")
            return False
        
        try:
            # Acquire Gmail API credentials
            creds = self._get_gmail_credentials()
            if not creds:
                self._write_log("ERROR Email send aborted: credentials unavailable")
                return False
            
            # Build Gmail service
            service = build('gmail', 'v1', credentials=creds)
            
            # Construct MIME message
            message = MIMEMultipart()
            message['to'] = self.config["to_email"]
            message['subject'] = f"[Task Manager] {subject}"
            
            # Email body
            if task_id:
                task_info = f"Task ID: {task_id}\n"
            else:
                task_info = ""
            
            full_body = f"{task_info}\n{body}"
            
            # Send as HTML
            html_body = f"""
            <html>
            <body>
                <pre style="font-family: 'Courier New', monospace; font-size: 12px; white-space: pre-wrap; background-color: #f5f5f5; padding: 10px; border-radius: 5px;">
{full_body}
                </pre>
            </body>
            </html>
            """
            
            message.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # Encode for Gmail API
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            self._write_log(f"INFO Sending email to={self.config.get('to_email','')} subject={subject} task_id={task_id}")
            # Send via Gmail API
            send_message = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            print(f"📧 Email sent: {subject}")
            print(f"📧 Message ID: {send_message['id']}")
            self._write_log(f"INFO Email sent successfully; message_id={send_message.get('id','<unknown>')}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            self._write_log(f"ERROR Failed to send email: {e}")
            return False
    
    def send_task_completion_email(self, task_id: str, status: str):
        """Send task completion email for given status"""
        if not self.config.get("enabled", False):
            return
        
        status_messages = {
            'completed': 'Task completed',
            'failed': 'Task failed',
            'killed': 'Task killed'
        }
        
        subject = status_messages.get(status, f'Task status changed: {status}')
        body = f"Task {task_id} status changed to: {status}"
        
        self.send_email(subject, body, task_id)
    
    def test_email(self) -> bool:
        """Send a test email to verify configuration"""
        return self.send_email("Test Email", "This is a test email from Task Manager.", "test")
