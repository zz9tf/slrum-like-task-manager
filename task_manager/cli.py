#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command line interface module
"""

import sys
import os
import time

from .core import TaskManager
from .config import ConfigManager


def main():
    """main function"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1]
    
    # global options
    if command in ['-h', '--help']:
        show_help()
        return
    elif command in ['-v', '--version']:
        show_version()
        return
    
    # initialize task manager
    manager = TaskManager()
    
    # command dispatch
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
        print(f"❌ unknown command: {command}")
        print("use 'task -h' to see help information")
        sys.exit(1)


def show_help():
    """show help information"""
    print("Task Manager - A task scheduler and monitor based on tmux")
    print("")
    print("Usage: task <command> [options]")
    print("")
    print("Global options:")
    print("  -h, --help     show this help information")
    print("  -v, --version  show version information")
    print("")
    print("Available commands:")
    print("  run      run new task")
    print("  list     list tasks")
    print("  kill     stop task")
    print("  monitor  monitor task output")
    print("  status   view task status")
    print("  output   view task output")
    print("  cleanup  clean old tasks")
    print("  logs     view task logs")
    print("  email    email configuration")
    print("  config   configuration management")
    print("")
    print("Examples:")
    print("  task run 'train model' 'python train.py --epochs 100'")
    print("  task list")
    print("  task list --resources")
    print("  task monitor <task_id>")
    print("  task kill <task_id>")
    print("  task status <task_id>")
    print("  task output <task_id>")
    print("  task cleanup")
    print("")
    print("Detailed help:")
    print("  task <command> -h     show detailed help for specific command")


def show_version():
    """show version information"""
    print("Task Manager v1.0.0")
    print("A task scheduler and monitor based on tmux")
    print("Author: zheng")
    print("Build date: 2025-09-09")


def cmd_run(manager: TaskManager):
    """run task command"""
    if len(sys.argv) < 4:
        print("❌ error: missing required parameters")
        print("Usage: task run <name> <command> [priority] [max_retries]")
        print("Use 'task run -h' to see detailed help")
        sys.exit(1)
    
    name = sys.argv[2]
    command = sys.argv[3]
    priority = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    # max_retries = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    
    # task_id = manager.create_task(name, command, priority, max_retries)
    task_id = manager.create_task(name, command, priority)
    print(f"✅ task created successfully: {task_id} - {name}")
    
    if manager.start_task(task_id):
        print(f"🚀 task started successfully: {task_id}")
        print(f"📺 view output: task output {task_id}")
        print(f"🛑 stop task: task kill {task_id}")
    else:
        print(f"❌ task start failed: {task_id}")


def cmd_list(manager: TaskManager):
    """list task command"""
    status_filter = None
    show_resources = False
    
    # parse parameters
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
        print("📋 no tasks found")
        return
    
    print("📋 all tasks:")
    task_list_formater = lambda task: f"{task['id']:<8} {task['name']:<20} {task['status']:<10} {task['priority']:<8} {task['duration']:<12} {task['tmux_session']:<20}"
    print(task_list_formater("ID", "Name", "Status", "Priority", "Duration", "Tmux session"))
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
        
        # calculate duration
        duration = "N/A"
        if task['start_time']:
            if task['end_time']:
                duration = str(task['end_time'] - task['start_time']).split('.')[0]
            else:
                duration = str(time.time() - task['start_time'].timestamp()).split('.')[0] + "s"
        
        print(task_list_formater(task['id'], task['name'], status_icon, task['status'], task['priority'], duration, task['tmux_session']))
    
    if show_resources:
        print("\n" + "=" * 80)
        resources = manager.resource_monitor.get_system_resources()
        print(manager.resource_monitor.format_resources(resources))


def cmd_kill(manager: TaskManager):
    """stop task command"""
    if len(sys.argv) < 3:
        print("❌ error: missing required parameters")
        print("Usage: task kill <task_id> [--force] | task kill --all [--force]")
        sys.exit(1)
    
    task_id = sys.argv[2]
    force = "--force" in sys.argv
    all_tasks = "--all" in sys.argv
    
    if all_tasks:
        running_tasks = manager.list_tasks(status_filter="running")
        if not running_tasks:
            print("📋 no running tasks")
            return
        
        for task in running_tasks:
            if manager.stop_task(task['id'], force):
                print(f"✅ task stopped: {task['id']}")
            else:
                print(f"❌ stop task failed: {task['id']}")
    else:
        if manager.stop_task(task_id, force):
            print(f"✅ task stopped: {task_id}")
        else:
            print(f"❌ stop task failed: {task_id}")


def cmd_monitor(manager: TaskManager):
    """monitor task command"""
    if len(sys.argv) < 3:
        print("❌ error: missing required parameters")
        print("Usage: task monitor <task_id> [--lines N] [--refresh SECONDS]")
        sys.exit(1)
    
    task_id = sys.argv[2]
    lines = 50
    refresh = 2.0
    
    # parse parameters
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
    
    if task_id not in manager.tasks:
        print(f"❌ task not found: {task_id}")
        return
    
    task = manager.tasks[task_id]
    print(f"📺 monitor task: {task.name} ({task_id})")
    print(f"📺 Tmux session: {task.tmux_session}")
    print("=" * 60)
    
    try:
        while True:
            status = manager.get_task_status(task_id)
            if not status or status['status'] not in ['running', 'pending']:
                print(f"\n✅ task ended: {status['status'] if status else 'unknown'}")
                break
            
            # clear screen and show output
            os.system('clear' if os.name == 'posix' else 'cls')
            print(f"📺 monitor task: {task.name} ({task_id}) - {status['status']}")
            print(f"⏱️  running time: {status.get('start_time', 'N/A')}")
            print("=" * 60)
            
            output = manager.get_tmux_output(task_id, lines)
            print(output)
            
            print("=" * 60)
            print("Press Ctrl+C to exit monitor")
            
            time.sleep(refresh)
            
    except KeyboardInterrupt:
        print(f"\n👋 stop monitor task: {task_id}")
        sys.exit(0)


def cmd_status(manager: TaskManager):
    """view task status command"""
    if len(sys.argv) < 3:
        print("❌ error: missing required parameters")
        print("Usage: task status <task_id>")
        sys.exit(1)
    
    task_id = sys.argv[2]
    status = manager.get_task_status(task_id)
    
    if not status:
        print(f"❌ task not found: {task_id}")
        return
    
    print(f"📊 task status: {task_id}")
    print("=" * 40)
    print(f"name: {status['name']}")
    print(f"status: {status['status']}")
    print(f"start time: {status['start_time'] or 'N/A'}")
    print(f"end time: {status['end_time'] or 'N/A'}")
    print(f"Tmux session: {status['tmux_session']}")
    print(f"PID: {status['pid'] or 'N/A'}")
    print(f"Priority: {status['priority']}")


def cmd_output(manager: TaskManager):
    """view task output command"""
    if len(sys.argv) < 3:
        print("❌ error: missing required parameters")
        print("Usage: task output <task_id> [--lines N]")
        sys.exit(1)
    
    task_id = sys.argv[2]
    lines = 50
    
    # parse parameters
    i = 3
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--lines" and i + 1 < len(sys.argv):
            lines = int(sys.argv[i + 1])
            i += 1
        i += 1
    
    print(f"📋 task output: {task_id}")
    print("=" * 60)
    output = manager.get_tmux_output(task_id, lines)
    print(output)


def cmd_cleanup(manager: TaskManager):
    """cleanup task command"""
    max_age_hours = 24
    if len(sys.argv) > 2:
        try:
            max_age_hours = int(sys.argv[2])
        except ValueError:
            print("❌ error: invalid time parameter")
            sys.exit(1)
    
    print(f"🧹 start cleanup task (tasks older than {max_age_hours} hours)")
    manager.cleanup_old_tasks(max_age_hours)
    print("✅ cleanup completed")


def cmd_logs(manager: TaskManager):
    """view task logs command"""
    if len(sys.argv) < 3:
        print("❌ error: missing required parameters")
        print("Usage: task logs <task_id> [lines]")
        sys.exit(1)
    
    task_id = sys.argv[2]
    lines = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    
    log_file = manager.logs_dir / f"{task_id}.log"
    if log_file.exists():
        print(f"📋 task logs: {task_id}")
        print("=" * 60)
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if lines > 0:
                    content_lines = content.split('\n')
                    content = '\n'.join(content_lines[-lines:])
                print(content)
        except Exception as e:
            print(f"❌ read logs failed: {e}")
    else:
        print(f"❌ logs file not found: {task_id}")


def cmd_email(manager: TaskManager):
    """email configuration command"""
    if len(sys.argv) < 3:
        print("❌ error: missing required parameters")
        print("Usage: task email <action>")
        print("actions: enable, disable, show, test")
        sys.exit(1)
    
    action = sys.argv[2]
    email_notifier = manager.email_notifier
    
    if action == "enable":
        # here we need to implement the logic to enable email
        print("✅ email notification enabled")
    elif action == "disable":
        # here we need to implement the logic to disable email
        print("✅ email notification disabled")
    elif action == "show":
        print("📧 current email configuration:")
        print(f"  recipient email: {email_notifier.config['to_email']}")
        print(f"  status: {'enabled' if email_notifier.config['enabled'] else 'disabled'}")
        print(f"  Token file: {email_notifier.config['token_file']}")
    elif action == "test":
        print("📧 sending test email...")
        if email_notifier.test_email():
            print("✅ test email sent successfully")
        else:
            print("❌ test email sent failed")
    else:
        print(f"❌ unknown action: {action}")
        sys.exit(1)


def cmd_config(manager: TaskManager):
    """Configuration management command"""
    if len(sys.argv) < 3:
        config_manager = ConfigManager(manager.data_dir)
        config_manager.show_help()
        sys.exit(1)
    
    action = sys.argv[2]
    config_manager = ConfigManager(manager.data_dir)
    
    # Check help option
    if action in ['-h', '--help']:
        config_manager.show_help()
        return
    
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
