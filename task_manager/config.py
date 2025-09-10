#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Management Module
"""

import json
import shutil
import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional

# Gmail API imports
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False


class ConfigManager:
    """Configuration Manager"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.config_dir = self.data_dir / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def init_config(self) -> bool:
        """Initialize configuration files"""
        print("🔧 Initializing task manager configuration...")
        
        # Create default email config
        email_config_file = self.config_dir / "email_config.json"
        if not email_config_file.exists():
            default_email_config = {
                "enabled": False,
                "to_email": ""
            }
            with open(email_config_file, 'w', encoding='utf-8') as f:
                json.dump(default_email_config, f, indent=4, ensure_ascii=False)
            print("✅ Email config file created: email_config.json")
        else:
            print("ℹ️  Email config file already exists: email_config.json")
        
        
        # Create credentials template
        credentials_file = self.config_dir / "credentials.json"
        if not credentials_file.exists():
            credentials_template = {
                "installed": {
                    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
                    "project_id": "your-project-id",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_secret": "YOUR_CLIENT_SECRET",
                    "redirect_uris": ["http://localhost"]
                }
            }
            with open(credentials_file, 'w', encoding='utf-8') as f:
                json.dump(credentials_template, f, indent=4, ensure_ascii=False)
            print("✅ Google API credentials template created: credentials.json")
        else:
            print("ℹ️  Google API credentials file already exists: credentials.json")
        
        print("")
        print("📝 Configuration file locations:")
        print(f"  Email config: {email_config_file}")
        print(f"  Google credentials: {credentials_file}")
        print("")
        print("🔧 Next steps:")
        print("  1. Edit credentials.json with your Google API credentials")
        print("  2. Use 'task config google_api login' to get token")
        print("  3. Use 'task config email <config_file>' to import email config")
        print("  4. Use 'task config test' to test email sending")
        
        return True
    
    def import_email_config(self, config_file: str) -> bool:
        """Import email configuration"""
        source_file = Path(config_file)
        if not source_file.exists():
            print(f"❌ Config file not found: {config_file}")
            return False
        
        try:
            # Read source config file
            with open(source_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Validate config format - support both formats
            if 'email' in config:
                # command_monitor_config.json format
                email_config = config['email']
                if 'to_email' not in email_config:
                    print("❌ Email config format error: missing 'to_email' field")
                    return False
            else:
                # Direct email_config.json format
                email_config = config
                if 'to_email' not in email_config:
                    print("❌ Email config format error: missing 'to_email' field")
                    return False
            
            # Save as email_config.json
            target_file = self.config_dir / "email_config.json"
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(email_config, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Email config imported: {target_file}")
            print(f"  Recipient email: {email_config['to_email']}")
            print(f"  Status: {'Enabled' if email_config.get('enabled', False) else 'Disabled'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to import email config: {e}")
            return False
    
    def import_token(self, token_file: str) -> bool:
        """Import Gmail token"""
        source_file = Path(token_file)
        if not source_file.exists():
            print(f"❌ Token file not found: {token_file}")
            return False
        
        try:
            # Validate token file format
            with open(source_file, 'r', encoding='utf-8') as f:
                token_data = json.load(f)
            
            required_fields = ['token', 'refresh_token', 'client_id', 'client_secret']
            for field in required_fields:
                if field not in token_data:
                    print(f"❌ Token file format error: missing '{field}' field")
                    return False
            
            # Copy to task manager config directory
            target_file = self.config_dir / "token.json"
            shutil.copy2(source_file, target_file)
            
            print(f"✅ Gmail token imported: {target_file}")
            print("  Email notifications are now available")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to import token: {e}")
            return False
    
    def setup_google_api(self, credentials_file: str) -> bool:
        """Setup Google API credentials"""
        source_file = Path(credentials_file)
        if not source_file.exists():
            print(f"❌ Credentials file not found: {credentials_file}")
            return False
        
        try:
            # Validate credentials file format
            with open(source_file, 'r', encoding='utf-8') as f:
                creds_data = json.load(f)
            
            if 'installed' not in creds_data:
                print("❌ Credentials file format error: missing 'installed' field")
                return False
            
            installed = creds_data['installed']
            required_fields = ['client_id', 'client_secret', 'redirect_uris']
            for field in required_fields:
                if field not in installed:
                    print(f"❌ Credentials file format error: missing '{field}' field")
                    return False
            
            # Copy to task manager config directory
            target_file = self.config_dir / "credentials.json"
            shutil.copy2(source_file, target_file)
            
            print(f"✅ Google API credentials imported: {target_file}")
            print("  Now you can use 'task config google_api login' to get token")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to import credentials: {e}")
            return False
    
    def google_api_login(self) -> bool:
        """Login via Google API to get token"""
        if not GMAIL_API_AVAILABLE:
            print("❌ Gmail API library not available")
            print("Please install: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
            return False
        
        credentials_file = self.config_dir / "credentials.json"
        token_file = self.config_dir / "token.json"
        
        if not credentials_file.exists():
            print("❌ Credentials file not found")
            print("Please use 'task config google_api file <credentials_file>' to import credentials file first")
            return False
        
        try:
            SCOPES = ['https://www.googleapis.com/auth/gmail.send']
            
            # Create OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_file), SCOPES)
            
            print("🌐 Opening browser for OAuth authorization...")
            print("If browser doesn't open automatically, please visit the displayed URL manually")
            
            # Run OAuth flow
            creds = flow.run_local_server(port=0)
            
            # Save credentials
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
            
            print(f"✅ Login successful! Token saved to: {token_file}")
            print("  Email notifications are now available")
            
            return True
            
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False
    
    def show_config(self) -> None:
        """Show current configuration"""
        print("📋 Current configuration:")
        print("=" * 50)
        
        # Email config
        email_config_file = self.config_dir / "email_config.json"
        if email_config_file.exists():
            try:
                with open(email_config_file, 'r', encoding='utf-8') as f:
                    email_config = json.load(f)
                print("📧 Email configuration:")
                print(f"  Recipient email: {email_config.get('to_email', 'Not set')}")
                print(f"  Status: {'Enabled' if email_config.get('enabled', False) else 'Disabled'}")
                print(f"  Config file: {email_config_file}")
            except Exception as e:
                print(f"❌ Failed to read email config: {e}")
        else:
            print("📧 Email configuration: Not configured")
        
        # Token config
        token_file = self.config_dir / "token.json"
        if token_file.exists():
            try:
                with open(token_file, 'r', encoding='utf-8') as f:
                    token_data = json.load(f)
                print("\n🔑 Gmail Token:")
                print(f"  Status: Configured")
                print(f"  Expiry: {token_data.get('expiry', 'Unknown')}")
                print(f"  Token file: {token_file}")
            except Exception as e:
                print(f"\n❌ Failed to read token: {e}")
        else:
            print("\n🔑 Gmail Token: Not configured")
        
        # Google API credentials
        credentials_file = self.config_dir / "credentials.json"
        if credentials_file.exists():
            try:
                with open(credentials_file, 'r', encoding='utf-8') as f:
                    creds_data = json.load(f)
                installed = creds_data.get('installed', {})
                client_id = installed.get('client_id', 'Not set')
                if client_id != 'YOUR_CLIENT_ID.apps.googleusercontent.com':
                    print(f"\n🔐 Google API credentials:")
                    print(f"  Status: Configured")
                    print(f"  Client ID: {client_id}")
                    print(f"  Credentials file: {credentials_file}")
                else:
                    print(f"\n🔐 Google API credentials: Not configured (using template)")
            except Exception as e:
                print(f"\n❌ Failed to read credentials: {e}")
        else:
            print("\n🔐 Google API credentials: Not configured")
        
        print("\n📁 Configuration directory:")
        print(f"  {self.data_dir}")
    
    def test_config(self) -> bool:
        """Test configuration by sending a real test email if possible"""
        print("🧪 Testing configuration...")
        
        # Check email config
        email_config_file = self.config_dir / "email_config.json"
        if not email_config_file.exists():
            print("❌ Email configuration not set")
            return False
        
        try:
            with open(email_config_file, 'r', encoding='utf-8') as f:
                email_config = json.load(f)
            
            if not email_config.get('enabled', False):
                print("❌ Email notifications not enabled")
                return False
            
            if not email_config.get('to_email'):
                print("❌ No recipient email set")
                return False
            
            # Check token
            token_file = self.config_dir / "token.json"
            if not token_file.exists():
                print("❌ Gmail token not configured")
                return False
            
            print("✅ Configuration check passed")
            print("📧 Sending test email...")
            
            # Attempt to send a real test email using EmailNotifier
            try:
                from .email import EmailNotifier
                notifier = EmailNotifier(self.data_dir)
                if notifier.test_email():
                    print("✅ Email sent successfully! Configuration is correct")
                    return True
                else:
                    print("❌ Failed to send test email. Check token or Gmail API setup")
                    return False
            except Exception as e:
                print(f"❌ Failed to invoke email notifier: {e}")
                return False
            
        except Exception as e:
            print(f"❌ Configuration test failed: {e}")
            return False
    
    def show_help(self) -> None:
        """Show configuration help information"""
        print("Configuration Management Help")
        print("=" * 50)
        print("")
        print("Available actions:")
        print("  init                           Initialize configuration files")
        print("  email <config_file>            Configure email settings")
        print("  token <token_file>             Configure Gmail token")
        print("  google_api file <creds_file>   Configure Google API credentials")
        print("  google_api login               Login via Google API to get token")
        print("  show                           Show current configuration")
        print("  test                           Test email sending")
        print("  -h, --help                     Show this help information")
        print("")
        print("Examples:")
        print("  task config init")
        print("  task config email ~/my_email_config.json")
        print("  task config token ~/my_token.json")
        print("  task config google_api file ~/credentials.json")
        print("  task config google_api login")
        print("  task config show")
        print("")
        print("Configuration directory: ~/.task_manager/config/")
        print("")
        print("Email Configuration Setup:")
        print("1. Create email_config.json with your email settings:")
        print('   {"enabled": true, "to_email": "your-email@example.com"}')
        print("")
        print("2. Get Google API credentials:")
        print("   - Go to Google Cloud Console")
        print("   - Enable Gmail API")
        print("   - Create OAuth 2.0 credentials")
        print("   - Download credentials.json")
        print("")
        print("3. Import credentials and login:")
        print("   task config google_api file ~/credentials.json")
        print("   task config google_api login")
        print("")
        print("4. Test configuration:")
        print("   task config test")
