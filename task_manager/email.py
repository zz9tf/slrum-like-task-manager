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
    
    def _get_task_log_content(self, task_id: str) -> str:
        """Get task log content for embedding in email"""
        try:
            log_file = self.data_dir / "logs" / f"{task_id}.log"
            if not log_file.exists():
                return ""
            
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            # Limit log content length to avoid email being too large
            max_log_lines = 200
            log_lines = log_content.split('\n')
            
            if len(log_lines) > max_log_lines:
                # Keep first 100 lines and last 100 lines with truncation notice
                truncated_log = '\n'.join(log_lines[:100]) + \
                              f'\n\n... [省略 {len(log_lines) - max_log_lines} 行日志] ...\n\n' + \
                              '\n'.join(log_lines[-100:])
                return truncated_log
            
            return log_content
            
        except Exception as e:
            self._write_log(f"WARNING Failed to read log file for task {task_id}: {e}")
            return ""
    
    def send_email(self, subject: str, body: str, task_id: str, duration: str, start_time: str, end_time: str, command: str) -> bool:
        """Send an email notification via Gmail API with log content embedded"""
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
            
            # Build complete email body with log content
            full_body = body
            
            # If task_id is provided, try to include log content
            if task_id:
                log_content = self._get_task_log_content(task_id)
                if log_content:
                    full_body += f"""

详细日志内容:
{'='*60}
{log_content}
{'='*60}

Notice: This is the complete execution log, which can be previewed in the email.
If you need the complete log file, please check the server path: ~/.task_manager/logs/{task_id}.log
                    """
                    self._write_log(f"INFO Log content embedded in email ({len(log_content.split(chr(10)))} lines)")
                else:
                    full_body += f"\n\nNote: Unable to read task log file {task_id}.log"
            
            # Send as HTML with proper formatting
            html_body = f"""
            <html>
            <body>
                <div style="font-family: Arial, sans-serif; line-height: 1.6;">
                    <h2 style="color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px;">
                        Task Manager Notification
                    </h2>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                        <h3 style="color: #007acc; margin-top: 0;">Task Info</h3>
                        <p><strong>Task ID:</strong> {task_id}</p>
                        <p><strong>Command:</strong> {command}</p>
                        <p><strong>Status:</strong> {subject}</p>
                        <p><strong>Duration:</strong> {duration}</p>
                        <p><strong>start time:</strong> {start_time}</p>
                        <p><strong>end time:</strong> {end_time}</p>
                    </div>
                    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0;">
                        <h3 style="color: #007acc; margin-top: 0;">Detailed Information</h3>
                        <pre style="font-family: 'Courier New', monospace; font-size: 12px; white-space: pre-wrap; margin: 0; overflow-x: auto;">{full_body}</pre>
                    </div>
                    <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #ddd; color: #666; font-size: 12px;">
                        <p>This email is sent by Task Manager</p>
                        <p>System time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                </div>
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
    
    def send_task_completion_email(self, task_id: str, status: str, duration: str, start_time: str, end_time: str, command: str):
        """Send task completion email for given status"""
        if not self.config.get("enabled", False):
            return
        
        status_messages = {
            'completed': 'Task completed',
            'failed': 'Task failed',
            'killed': 'Task killed'
        }
        
        subject = status_messages.get(status, f'Task status changed: {status}')
        body = f"Task {task_id} status changed to: {status}\nDuration: {duration}\nStart time: {start_time}\nEnd time: {end_time}\nCommand: {command}"
        
        self.send_email(subject, body, task_id, duration, start_time, end_time, command)
    
    def test_email(self) -> bool:
        """Send a test email to verify configuration"""
        return self.send_email(
            "Test Email", 
            "This is a test email from Task Manager.", 
            "test",
            "N/A",
            "N/A", 
            "N/A",
            "test command"
        )
