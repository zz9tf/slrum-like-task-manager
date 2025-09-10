#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件通知模块
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
    """邮件通知器"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """加载邮件配置"""
        # 只使用email_config.json
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
                print(f"⚠️ 加载邮件配置失败: {e}")
        
        # 默认配置
        return {
            "enabled": False,
            "to_email": "",
            "token_file": str(token_file)
        }
    
    def _get_gmail_credentials(self):
        """获取Gmail API凭据"""
        if not GMAIL_API_AVAILABLE:
            print("❌ Gmail API库不可用")
            return None
        
        SCOPES = ['https://www.googleapis.com/auth/gmail.send']
        creds = None
        token_file = self.config.get("token_file")
        
        if not token_file or not Path(token_file).exists():
            print(f"❌ Token文件不存在: {token_file}")
            return None
        
        try:
            # 加载现有token
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            
            # 如果token无效，尝试刷新
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    print("🔄 刷新过期token...")
                    creds.refresh(Request())
                    # 保存刷新后的凭据
                    with open(token_file, 'w') as token:
                        token.write(creds.to_json())
                    print("✅ Token刷新成功")
                else:
                    print("❌ 无有效凭据")
                    return None
            
            return creds
            
        except Exception as e:
            print(f"❌ 加载Gmail凭据失败: {e}")
            return None
    
    def send_email(self, subject: str, body: str, task_id: str = None) -> bool:
        """发送邮件通知"""
        if not self.config.get("enabled", False):
            return False
        
        if not GMAIL_API_AVAILABLE:
            print("❌ Gmail API库不可用")
            return False
        
        try:
            # 获取Gmail API凭据
            creds = self._get_gmail_credentials()
            if not creds:
                return False
            
            # 构建Gmail服务
            service = build('gmail', 'v1', credentials=creds)
            
            # 创建邮件消息
            message = MIMEMultipart()
            message['to'] = self.config["to_email"]
            message['subject'] = f"[任务管理器] {subject}"
            
            # 邮件正文
            if task_id:
                task_info = f"任务ID: {task_id}\n"
            else:
                task_info = ""
            
            full_body = f"{task_info}\n{body}"
            
            # 使用HTML格式发送邮件
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
            
            # 编码消息用于Gmail API
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # 使用Gmail API发送消息
            send_message = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            print(f"📧 邮件发送成功: {subject}")
            print(f"📧 消息ID: {send_message['id']}")
            return True
            
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
            return False
    
    def send_task_completion_email(self, task_id: str, status: str):
        """发送任务完成邮件"""
        if not self.config.get("enabled", False):
            return
        
        status_messages = {
            'completed': '任务已完成',
            'failed': '任务执行失败',
            'killed': '任务被终止'
        }
        
        subject = status_messages.get(status, f'任务状态变化: {status}')
        body = f"任务 {task_id} 状态已变更为: {status}"
        
        self.send_email(subject, body, task_id)
    
    def test_email(self) -> bool:
        """测试邮件发送"""
        return self.send_email("测试邮件", "这是一封来自任务管理器的测试邮件。", "test")
