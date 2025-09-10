# Task Management System

A tmux-based task scheduling and monitoring tool with support for concurrent execution, real-time monitoring, email notifications, and more.

## Features

- 🚀 **Concurrent Execution**: Support for multiple tasks running simultaneously
- 📊 **Real-time Monitoring**: Real-time task status and output viewing
- 🛠️ **Resource Monitoring**: CPU, memory, and disk usage monitoring
- 📝 **Log Management**: Automatic task output and log recording
- 🔧 **Configuration Management**: Simple configuration file management
- 📧 **Email Notifications**: Automatic email notifications when tasks complete (requires configuration)

## Installation

### System Requirements

- Python 3.7+
- tmux (required)

### Check tmux

Before installation, ensure tmux is installed on your system:

```bash
# Check if tmux is installed
tmux --version

# If not installed, install tmux first
# Ubuntu/Debian:
sudo apt-get install tmux

# CentOS/RHEL:
sudo yum install tmux

# macOS:
brew install tmux
```

### Quick Installation

```bash
# Clone repository
git clone <repository-url>
cd task_manager

# Run installation script
chmod +x install.sh
./install.sh
```

### Manual Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install package
pip install -e .

# Initialize configuration
task config init
```

## Usage

### Basic Commands

```bash
# Run new task
task run "Task Name" "command to execute"

# List all tasks
task list

# Monitor task output in real-time
task monitor <task_id>

# Stop task
task kill <task_id>

# View task status
task status <task_id>

# View task output
task output <task_id>

# Clean up old tasks
task cleanup

# View help
task -h
```

### Examples

```bash
# Run a training task
task run "Model Training" "python train.py --epochs 100"

# Run multiple tasks concurrently
task run "Data Processing" "python process_data.py" &
task run "Feature Extraction" "python extract_features.py" &

# Monitor running tasks
task list --resources

# Monitor specific task
task monitor 00001

# Stop all running tasks
task kill --all
```

## Configuration

### Email Notifications

To enable email notifications, you need to configure three files:

#### 1. Email Configuration File

Create `~/.task_manager/config/email_config.json`:

```json
{
    "enabled": true,
    "to_email": "your-email@example.com"
}
```

#### 2. Google API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download credentials file as `credentials.json`
6. Place it in `~/.task_manager/config/credentials.json`

#### 3. Gmail Token

Use the following command to get the token:

```bash
# Login via Google API to get token
task config google_api login
```

#### Quick Import Method

If you already have the configuration files:

```bash
# Import email configuration
task config email ~/my_email_config.json

# Import Gmail token
task config token ~/my_token.json

# Import Google API credentials
task config google_api file ~/credentials.json
```

### Configuration Management

```bash
# Initialize configuration files
task config init

# Show current configuration
task config show

# Test email configuration
task config test

# Import email configuration
task config email <config_file>

# Import Gmail token
task config token <token_file>

# Setup Google API credentials
task config google_api file <credentials_file>

# Login via Google API
task config google_api login
```

## Command Reference

### Global Options

- `-h, --help`: Show help information
- `-v, --version`: Show version information

### Commands

#### `task run <name> <command> [priority] [max_retries]`

Run new task.

**Parameters:**
- `name`: Task name
- `command`: Command to execute
- `priority`: Task priority (0-10, default 0)
- `max_retries`: Maximum retry count (default 0)

**Examples:**
```bash
task run "Train Model" "python train.py"
task run "Important Task" "python important.py" 10
task run "May Fail" "python unstable.py" 0 3
```

#### `task list [options]`

List all tasks.

**Options:**
- `--status <status>`: Filter tasks by status
- `--resources`: Show system resource usage

**Examples:**
```bash
task list                    # List all tasks
task list --status running   # Show only running tasks
task list --resources        # Show tasks and resource info
```

#### `task kill <task_id> [--force] | task kill --all [--force]`

Stop task.

**Parameters:**
- `task_id`: Task ID to stop
- `--all`: Stop all running tasks
- `--force`: Force stop task

**Examples:**
```bash
task kill 00001              # Stop task 00001
task kill 00001 --force      # Force stop task 00001
task kill --all              # Stop all running tasks
```

#### `task monitor <task_id> [--lines N] [--refresh SECONDS]`

Real-time task monitoring.

**Parameters:**
- `task_id`: Task ID to monitor
- `--lines N`: Show last N lines of output (default 50)
- `--refresh S`: Refresh interval in seconds (default 2.0)

**Examples:**
```bash
task monitor 00001                    # Monitor task 00001
task monitor 00001 --lines 100        # Show last 100 lines
task monitor 00001 --refresh 1.0      # Refresh every second
```

#### `task status <task_id>`

View task status.

**Parameters:**
- `task_id`: Task ID to view status

**Examples:**
```bash
task status 00001    # View status of task 00001
```

#### `task output <task_id> [--lines N]`

View task output.

**Parameters:**
- `task_id`: Task ID to view output
- `--lines N`: Show last N lines of output (default 50)

**Examples:**
```bash
task output 00001              # View output of task 00001
task output 00001 --lines 100  # Show last 100 lines
```

#### `task cleanup [hours]`

Clean up completed tasks.

**Parameters:**
- `hours`: Clean up tasks completed more than specified hours ago (default 24)

**Examples:**
```bash
task cleanup        # Clean up tasks older than 24 hours
task cleanup 12     # Clean up tasks older than 12 hours
task cleanup 0      # Clean up all completed tasks
```

#### `task logs <task_id> [lines]`

View task logs.

**Parameters:**
- `task_id`: Task ID to view logs
- `lines`: Show last N lines of logs (default 100)

**Examples:**
```bash
task logs 00001        # View logs of task 00001
task logs 00001 50     # Show last 50 lines
```

#### `task email <action>`

Email notification management.

**Actions:**
- `enable`: Enable email notifications
- `disable`: Disable email notifications
- `show`: Show current email configuration
- `test`: Test email sending

**Examples:**
```bash
task email enable    # Enable email notifications
task email disable   # Disable email notifications
task email show      # View current configuration
task email test      # Send test email
```

#### `task config <action> [file_path]`

Configuration management.

**Actions:**
- `init`: Initialize configuration files
- `email <config_file>`: Configure email settings
- `token <token_file>`: Configure Gmail token
- `google_api file <creds_file>`: Configure Google API credentials
- `google_api login`: Login via Google API to get token
- `show`: Show current configuration
- `test`: Test email sending

**Examples:**
```bash
task config init
task config email ~/my_email_config.json
task config token ~/my_token.json
task config google_api file ~/credentials.json
task config google_api login
task config show
```

## Task Status

Tasks can have the following statuses:

- `pending`: Waiting to start
- `running`: Currently running
- `completed`: Successfully completed
- `failed`: Failed to complete
- `killed`: Manually stopped

## File Structure

```
~/.task_manager/
├── config/
│   ├── email_config.json    # Email configuration
│   ├── credentials.json     # Google API credentials
│   └── token.json          # Gmail token
├── logs/                   # Task log files
│   ├── 00001.log
│   └── 00002.log
└── tasks.json              # Task database
```

## Uninstallation

```bash
# Run uninstall script
chmod +x uninstall.sh
./uninstall.sh

# Or manually uninstall
pip uninstall task-manager
rm -rf ~/.task_manager
```

## Troubleshooting

### Common Issues

1. **tmux not found**: Install tmux using your package manager
2. **Permission denied**: Make sure you have execute permissions for scripts
3. **Email not working**: Check Gmail API configuration and token validity
4. **Task not starting**: Check if tmux session name conflicts exist

### Log Files

- Task logs: `~/.task_manager/logs/<task_id>.log`
- System logs: Check terminal output for error messages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Created by zheng

## Changelog

### v1.0.0 (2025-09-09)
- Initial release
- Basic task management functionality
- tmux integration
- Email notifications
- Resource monitoring
- Configuration management
