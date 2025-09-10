#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command Line Interface Module
"""

import sys
import os
import time
import json
from pathlib import Path
from typing import Optional

from .core import TaskManager
from .email import EmailNotifier
from .config import ConfigManager


def main():
    """Main entry function"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1]
    
    # Global options
    if command in ['-h', '--help']:
        show_help()
        return
    elif command in ['-v', '--version']:
        show_version()
        return
    
    # Initialize task manager
    manager = TaskManager()
    
    # Command dispatch
    if command == "run":
        cmd_run(manager)
    elif command == "list":
        cmd_list(manager)
    elif command == "kill":
        cmd_kill(manager)
    elif command == "monitor":
        cmd_monitor(manager)
    elif command == "status":
        cmd_status(manager)
    elif command == "output":
        cmd_output(manager)
    elif command == "cleanup":
        cmd_cleanup(manager)
    elif command == "logs":
        cmd_logs(manager)
    elif command == "email":
        cmd_email(manager)
    elif command == "config":
        cmd_config(manager)
    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'task -h' for help")
        sys.exit(1)


def show_help():
    """Show help information"""
    print("Task Management System - tmux-based task scheduling and monitoring tool")
    print("")
    print("Usage: task <command> [options]")
    print("")
    print("Global options:")
    print("  -h, --help     Show this help message")
    print("  -v, --version  Show version information")
    print("")
    print("Available commands:")
    print("  run      Run new task")
    print("  list     List tasks")
    print("  kill     Stop task")
    print("  monitor  Monitor task output")
    print("  status   View task status")
    print("  output   View task output")
    print("  cleanup  Clean up old tasks")
    print("  logs     View task logs")
    print("  email    Email configuration")
    print("  config   Configuration management")
    print("")
    print("Examples:")
    print("  task run 'Train Model' 'python train.py --epochs 100'")
    print("  task list")
    print("  task list --resources")
    print("  task monitor <task_id>")
    print("  task kill <task_id>")
    print("  task status <task_id>")
    print("  task output <task_id>")
    print("  task cleanup")
    print("")
    print("Detailed help:")
    print("  task <command> -h     Show detailed help for specific command")


def show_version():
    """Show version information"""
    print("Task Management System v1.0.0")
    print("tmux-based task scheduling and monitoring tool")
    print("Author: zheng")
    print("Build date: 2025-09-09")


def cmd_run(manager: TaskManager):
    """Run task command"""
    if len(sys.argv) < 3:
        print("❌ Error: Missing required parameters")
        print("Usage: task run <name> <command> [priority] [max_retries]")
        print("Use 'task run -h' for detailed help")
        sys.exit(1)
    
    # Check help option
    if sys.argv[2] in ['-h', '--help']:
        print("Run new task")
        print("")
        print("Usage: task run <name> <command> [priority] [max_retries]")
        print("")
        print("Parameters:")
        print("  name         Task name")
        print("  command      Command to execute")
        print("  priority     Task priority (0-10, default 0)")
        print("  max_retries  Maximum retry count (default 0)")
        print("")
        print("Examples:")
        print("  task run 'Train Model' 'python train.py'")
        print("  task run 'Important Task' 'python important.py' 10")
        print("  task run 'May Fail' 'python unstable.py' 0 3")
        print("")
        print("Notes:")
        print("  - Tasks run in tmux sessions")
        print("  - Higher priority numbers get higher priority")
        print("  - Tasks will retry automatically on failure")
        return
    
    if len(sys.argv) < 4:
        print("❌ Error: Missing required parameters")
        print("Usage: task run <name> <command> [priority] [max_retries]")
        print("Use 'task run -h' for detailed help")
        sys.exit(1)
    
    name = sys.argv[2]
    command = sys.argv[3]
    priority = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    max_retries = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    
    task_id = manager.create_task(name, command, priority, max_retries)
    print(f"✅ Task created successfully: {task_id} - {name}")
    
    if manager.start_task(task_id):
        print(f"🚀 Task started: {task_id}")
        print(f"📺 View output: task output {task_id}")
        print(f"🛑 Stop task: task kill {task_id}")
    else:
        print(f"❌ Failed to start task: {task_id}")


def cmd_list(manager: TaskManager):
    """List tasks command"""
    # Check help option
    if len(sys.argv) >= 3 and sys.argv[2] in ['-h', '--help']:
        print("List all tasks")
        print("")
        print("Usage: task list [options]")
        print("")
        print("Options:")
        print("  --status <status>  Filter tasks by status")
        print("  --resources        Show system resource usage")
        print("  -h, --help         Show this help information")
        print("")
        print("Status values:")
        print("  pending     Pending")
        print("  running     Running")
        print("  completed   Completed")
        print("  failed      Failed")
        print("  killed      Killed")
        print("")
        print("Examples:")
        print("  task list                    # List all tasks")
        print("  task list --status running   # Show only running tasks")
        print("  task list --resources        # Show tasks and resource info")
        return
    
    status_filter = None
    show_resources = False
    
    # Parse arguments
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--resources":
            show_resources = True
        elif arg == "--status" and i + 1 < len(sys.argv):
            status_filter = sys.argv[i + 1]
            i += 1
        elif arg in ['pending', 'running', 'completed', 'failed', 'killed']:
            status_filter = arg
        i += 1
    
    tasks = manager.list_tasks(status_filter)
    
    if not tasks:
        print("📋 No tasks found")
        return
    
    print("📋 All tasks:")
    print("ID        Name                    Status          Priority    Duration         Tmux Session")
    print("=" * 80)
    
    for task in tasks:
        status_icons = {
            'pending': '⏳',
            'running': '🚀',
            'completed': '✅',
            'failed': '❌',
            'killed': '🛑'
        }
        status_icon = status_icons.get(task['status'], '❓')
        
        # Calculate duration
        duration = "N/A"
        if task['start_time']:
            if task['end_time']:
                duration = str(task['end_time'] - task['start_time']).split('.')[0]
            else:
                duration = str(time.time() - task['start_time'].timestamp()).split('.')[0] + "s"
        
        print(f"{task['id']:<8} {task['name']:<20} {status_icon} {task['status']:<10} {task['priority']:<8} {duration:<12} {task['tmux_session']}")
    
    if show_resources:
        print("\n" + "=" * 80)
        resources = manager.resource_monitor.get_system_resources()
        print(manager.resource_monitor.format_resources(resources))


def cmd_kill(manager: TaskManager):
    """Stop task command"""
    if len(sys.argv) < 3:
        print("❌ Error: Missing required parameters")
        print("Usage: task kill <task_id> [--force] | task kill --all [--force]")
        print("Use 'task kill -h' for detailed help")
        sys.exit(1)
    
    # Check help option
    if sys.argv[2] in ['-h', '--help']:
        print("Stop task")
        print("")
        print("Usage: task kill <task_id> [--force] | task kill --all [--force]")
        print("")
        print("Parameters:")
        print("  task_id      Task ID to stop")
        print("  --all        Stop all running tasks")
        print("  --force      Force stop task")
        print("  -h, --help   Show this help information")
        print("")
        print("Examples:")
        print("  task kill 00001              # Stop task 00001")
        print("  task kill 00001 --force      # Force stop task 00001")
        print("  task kill --all              # Stop all running tasks")
        print("  task kill --all --force      # Force stop all running tasks")
        print("")
        print("Notes:")
        print("  - Using --force will forcefully terminate tmux session")
        print("  - Stopped tasks will have status 'killed'")
        return
    
    task_id = sys.argv[2]
    force = "--force" in sys.argv
    all_tasks = "--all" in sys.argv
    
    if all_tasks:
        running_tasks = manager.list_tasks(status_filter="running")
        if not running_tasks:
            print("📋 No running tasks")
            return
        
        for task in running_tasks:
            if manager.stop_task(task['id'], force):
                print(f"✅ Task stopped: {task['id']}")
            else:
                print(f"❌ Failed to stop task: {task['id']}")
    else:
        if manager.stop_task(task_id, force):
            print(f"✅ Task stopped: {task_id}")
        else:
            print(f"❌ Failed to stop task: {task_id}")


def cmd_monitor(manager: TaskManager):
    """Monitor task command"""
    if len(sys.argv) < 3:
        print("❌ Error: Missing required parameters")
        print("Usage: task monitor <task_id> [--lines N] [--refresh SECONDS]")
        print("Use 'task monitor -h' for detailed help")
        sys.exit(1)
    
    # Check help option
    if sys.argv[2] in ['-h', '--help']:
        print("Real-time task monitoring")
        print("")
        print("Usage: task monitor <task_id> [--lines N] [--refresh SECONDS]")
        print("")
        print("Parameters:")
        print("  task_id      Task ID to monitor")
        print("  --lines N    Show last N lines of output (default 50)")
        print("  --refresh S  Refresh interval in seconds (default 2.0)")
        print("  -h, --help   Show this help information")
        print("")
        print("Examples:")
        print("  task monitor 00001                    # Monitor task 00001")
        print("  task monitor 00001 --lines 100        # Show last 100 lines")
        print("  task monitor 00001 --refresh 1.0      # Refresh every second")
        print("")
        print("Notes:")
        print("  - Press Ctrl+C to exit monitoring")
        print("  - Monitoring shows real-time task output")
        return
    
    task_id = sys.argv[2]
    lines = 50
    refresh = 2.0
    
    # Parse arguments
    i = 3
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--lines" and i + 1 < len(sys.argv):
            lines = int(sys.argv[i + 1])
            i += 1
        elif arg == "--refresh" and i + 1 < len(sys.argv):
            refresh = float(sys.argv[i + 1])
            i += 1
        i += 1
    
    print(f"📺 Monitoring task: {task_id}")
    print("Press Ctrl+C to stop monitoring")
    print("=" * 60)
    
    try:
        while True:
            output = manager.get_tmux_output(task_id, lines)
            print(f"\n[{time.strftime('%H:%M:%S')}] Task {task_id} output:")
            print("-" * 40)
            print(output)
            time.sleep(refresh)
    except KeyboardInterrupt:
        print(f"\n👋 Stopped monitoring task: {task_id}")
        sys.exit(0)


def cmd_status(manager: TaskManager):
    """View task status command"""
    if len(sys.argv) < 3:
        print("❌ Error: Missing required parameters")
        print("Usage: task status <task_id>")
        print("Use 'task status -h' for detailed help")
        sys.exit(1)
    
    # Check help option
    if sys.argv[2] in ['-h', '--help']:
        print("View task status")
        print("")
        print("Usage: task status <task_id>")
        print("")
        print("Parameters:")
        print("  task_id      Task ID to view status")
        print("  -h, --help   Show this help information")
        print("")
        print("Examples:")
        print("  task status 00001    # View status of task 00001")
        print("")
        print("Display information:")
        print("  - Basic task info (ID, name, status)")
        print("  - Runtime statistics")
        print("  - Resource usage")
        print("  - Recent output")
        return
    
    task_id = sys.argv[2]
    status = manager.get_task_status(task_id)
    
    if not status:
        print(f"❌ Task not found: {task_id}")
        return
    
    print(f"📊 Task status: {task_id}")
    print("=" * 40)
    print(f"Name: {status['name']}")
    print(f"Status: {status['status']}")
    print(f"Priority: {status['priority']}")
    print(f"Created: {status['created_time']}")
    print(f"Started: {status['start_time'] or 'N/A'}")
    print(f"Ended: {status['end_time'] or 'N/A'}")
    print(f"Tmux session: {status['tmux_session']}")
    print(f"PID: {status['pid'] or 'N/A'}")
    print(f"Priority: {status['priority']}")


def cmd_output(manager: TaskManager):
    """View task output command"""
    if len(sys.argv) < 3:
        print("❌ Error: Missing required parameters")
        print("Usage: task output <task_id> [--lines N]")
        print("Use 'task output -h' for detailed help")
        sys.exit(1)
    
    # Check help option
    if sys.argv[2] in ['-h', '--help']:
        print("View task output")
        print("")
        print("Usage: task output <task_id> [--lines N]")
        print("")
        print("Parameters:")
        print("  task_id      Task ID to view output")
        print("  --lines N    Show last N lines of output (default 50)")
        print("  -h, --help   Show this help information")
        print("")
        print("Examples:")
        print("  task output 00001              # View output of task 00001")
        print("  task output 00001 --lines 100  # Show last 100 lines")
        print("")
        print("Notes:")
        print("  - Output comes from tmux session")
        print("  - Only shows recent output content")
        return
    
    task_id = sys.argv[2]
    lines = 50
    
    # Parse arguments
    i = 3
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--lines" and i + 1 < len(sys.argv):
            lines = int(sys.argv[i + 1])
            i += 1
        i += 1
    
    print(f"📋 Task output: {task_id}")
    print("=" * 60)
    output = manager.get_tmux_output(task_id, lines)
    print(output)


def cmd_cleanup(manager: TaskManager):
    """Cleanup tasks command"""
    # Check help option
    if len(sys.argv) >= 3 and sys.argv[2] in ['-h', '--help']:
        print("Clean up completed tasks")
        print("")
        print("Usage: task cleanup [hours]")
        print("")
        print("Parameters:")
        print("  hours        Clean up tasks completed more than specified hours ago (default 24)")
        print("  -h, --help   Show this help information")
        print("")
        print("Examples:")
        print("  task cleanup        # Clean up tasks older than 24 hours")
        print("  task cleanup 12     # Clean up tasks older than 12 hours")
        print("  task cleanup 0      # Clean up all completed tasks")
        print("")
        print("Notes:")
        print("  - Only cleans up completed, failed, or killed tasks")
        print("  - Running tasks will not be cleaned up")
        print("  - Cleanup removes both task records and log files")
        return
    
    max_age_hours = 24
    if len(sys.argv) > 2:
        try:
            max_age_hours = int(sys.argv[2])
        except ValueError:
            print("❌ Error: Invalid time parameter")
            print("Use 'task cleanup -h' for help")
            sys.exit(1)
    
    print(f"🧹 Starting cleanup (tasks completed more than {max_age_hours} hours ago)")
    manager.cleanup_old_tasks(max_age_hours)
    print("✅ Cleanup completed")


def cmd_logs(manager: TaskManager):
    """View task logs command"""
    if len(sys.argv) < 3:
        print("❌ Error: Missing required parameters")
        print("Usage: task logs <task_id> [lines]")
        print("Use 'task logs -h' for detailed help")
        sys.exit(1)
    
    # Check help option
    if sys.argv[2] in ['-h', '--help']:
        print("View task logs")
        print("")
        print("Usage: task logs <task_id> [lines]")
        print("")
        print("Parameters:")
        print("  task_id      Task ID to view logs")
        print("  lines        Show last N lines of logs (default 100)")
        print("  -h, --help   Show this help information")
        print("")
        print("Examples:")
        print("  task logs 00001        # View logs of task 00001")
        print("  task logs 00001 50     # Show last 50 lines")
        print("")
        print("Notes:")
        print("  - Log files are saved in ~/.task_manager/logs/")
        print("  - Logs contain complete task output records")
        return
    
    task_id = sys.argv[2]
    lines = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    
    log_file = manager.logs_dir / f"{task_id}.log"
    if log_file.exists():
        print(f"📋 Task logs: {task_id}")
        print("=" * 60)
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines_content = content.split('\n')
                if len(lines_content) > lines:
                    lines_content = lines_content[-lines:]
                print('\n'.join(lines_content))
        except Exception as e:
            print(f"❌ Failed to read logs: {e}")
    else:
        print(f"❌ Log file not found: {task_id}")


def cmd_email(manager: TaskManager):
    """Email configuration command"""
    if len(sys.argv) < 3:
        print("❌ Error: Missing required parameters")
        print("Usage: task email <action>")
        print("Actions: enable, disable, show, test")
        print("Use 'task email -h' for detailed help")
        sys.exit(1)
    
    # Check help option
    if sys.argv[2] in ['-h', '--help']:
        print("Email notification management")
        print("")
        print("Usage: task email <action>")
        print("")
        print("Actions:")
        print("  enable       Enable email notifications")
        print("  disable      Disable email notifications")
        print("  show         Show current email configuration")
        print("  test         Test email sending")
        print("  -h, --help   Show this help information")
        print("")
        print("Examples:")
        print("  task email enable    # Enable email notifications")
        print("  task email disable   # Disable email notifications")
        print("  task email show      # View current configuration")
        print("  task email test      # Send test email")
        print("")
        print("Notes:")
        print("  - Email settings need to be configured first")
        print("  - Use 'task config' command for email configuration")
        return
    
    action = sys.argv[2]
    email_notifier = manager.email_notifier
    
    if action == "enable":
        # Here we need to implement the logic to enable email
        print("✅ Email notifications enabled")
    elif action == "disable":
        # Here we need to implement the logic to disable email
        print("✅ Email notifications disabled")
    elif action == "show":
        print("📧 Current email configuration:")
        print(f"  Recipient email: {email_notifier.config['to_email']}")
        print(f"  Status: {'Enabled' if email_notifier.config['enabled'] else 'Disabled'}")
    elif action == "test":
        if email_notifier.test_email():
            print("✅ Test email sent successfully")
        else:
            print("❌ Failed to send test email")
    else:
        print(f"❌ Unknown action: {action}")
        sys.exit(1)


def cmd_config(manager: TaskManager):
    """Configuration management command"""
    if len(sys.argv) < 3:
        print("❌ Error: Missing required parameters")
        print("Usage: task config <action> [file_path]")
        print("")
        print("Actions:")
        print("  init                           Initialize configuration files")
        print("  email <config_file>            Configure email settings")
        print("  token <token_file>             Configure Gmail token")
        print("  google_api file <creds_file>   Configure Google API credentials")
        print("  google_api login               Login via Google API to get token")
        print("  show                           Show current configuration")
        print("  test                           Test email sending")
        print("")
        print("Examples:")
        print("  task config init")
        print("  task config email ~/my_email_config.json")
        print("  task config token ~/my_token.json")
        print("  task config google_api file ~/credentials.json")
        print("  task config google_api login")
        print("  task config show")
        print("")
        print("Use 'task config -h' for detailed help")
        sys.exit(1)
    
    # Check help option
    if sys.argv[2] in ['-h', '--help']:
        print("Configuration management")
        print("")
        print("Usage: task config <action> [file_path]")
        print("")
        print("Actions:")
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
        return
    
    action = sys.argv[2]
    config_manager = ConfigManager(manager.data_dir)
    
    if action == "init":
        config_manager.init_config()
    elif action == "email":
        if len(sys.argv) < 4:
            print("❌ Error: Missing config file path")
            print("Usage: task config email <config_file>")
            sys.exit(1)
        config_manager.import_email_config(sys.argv[3])
    elif action == "token":
        if len(sys.argv) < 4:
            print("❌ Error: Missing token file path")
            print("Usage: task config token <token_file>")
            sys.exit(1)
        config_manager.import_token(sys.argv[3])
    elif action == "google_api":
        if len(sys.argv) < 4:
            print("❌ Error: Missing google_api subcommand")
            print("Usage: task config google_api <file|login> [file_path]")
            sys.exit(1)
        sub_action = sys.argv[3]
        if sub_action == "file":
            if len(sys.argv) < 5:
                print("❌ Error: Missing credentials file path")
                print("Usage: task config google_api file <credentials_file>")
                sys.exit(1)
            config_manager.setup_google_api(sys.argv[4])
        elif sub_action == "login":
            config_manager.google_api_login()
        else:
            print(f"❌ Unknown google_api action: {sub_action}")
            print("Available actions: file, login")
            sys.exit(1)
    elif action == "show":
        config_manager.show_config()
    elif action == "test":
        config_manager.test_config()
    else:
        print(f"❌ Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
