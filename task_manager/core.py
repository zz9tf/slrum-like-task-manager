#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Manager Core Module - Simplified Implementation
"""

import json
import time
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import base64

from .email import EmailNotifier
from .monitor import ResourceMonitor


@dataclass
class Task:
    """Task data structure"""
    id: str
    name: str
    command: str
    tmux_session: str
    status: str = "pending"
    priority: int = 0
    max_retries: int = 0
    retry_count: int = 0
    created_time: datetime = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    pid: Optional[int] = None
    exit_code: Optional[int] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.created_time is None:
            self.created_time = datetime.now()


class TaskManager:
    """Task Manager - Simplified"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path.home() / ".task_manager"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logs directory
        self.logs_dir = self.data_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.email_notifier = EmailNotifier(self.data_dir)
        self.resource_monitor = ResourceMonitor()
        
        # Load tasks
        self.tasks_file = self.data_dir / "tasks.json"
        self.tasks = self._load_tasks()
        
        # Task ID counter
        self.next_task_id = self._get_next_task_id()
    
    def _load_tasks(self) -> Dict[str, Task]:
        """Load tasks from file"""
        if not self.tasks_file.exists():
            return {}
        
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                tasks = {}
                for task_id, task_data in data.items():
                    # Convert datetime strings back to datetime objects
                    for time_field in ['created_time', 'start_time', 'end_time']:
                        if task_data.get(time_field):
                            task_data[time_field] = datetime.fromisoformat(task_data[time_field])
                    tasks[task_id] = Task(**task_data)
                return tasks
        except Exception as e:
            print(f"⚠️ Failed to load tasks: {e}")
            return {}
    
    def _save_tasks(self):
        """Save tasks to file"""
        try:
            data = {}
            for task_id, task in self.tasks.items():
                task_dict = asdict(task)
                # Convert datetime objects to strings
                for time_field in ['created_time', 'start_time', 'end_time']:
                    if task_dict.get(time_field):
                        task_dict[time_field] = task_dict[time_field].isoformat()
                data[task_id] = task_dict
            
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Failed to save tasks: {e}")
    
    def _get_next_task_id(self) -> int:
        """Get next task ID"""
        if not self.tasks:
            return 1
        
        max_id = max(int(task_id) for task_id in self.tasks.keys())
        return max_id + 1
    
    @staticmethod
    def _escape_single_quotes(text: str) -> str:
        """Escape single quotes for safe inclusion inside bash -lc '...'."""
        return text.replace("'", "'\\''")
    
    def create_task(self, name: str, command: str, priority: int = 0, max_retries: int = 0) -> Optional[str]:
        """Create new task"""
        task_id = f"{self.next_task_id:05d}"
        tmux_session = f"task_{task_id}"
        
        task = Task(
            id=task_id,
            name=name,
            command=command,
            tmux_session=tmux_session,
            priority=priority,
            max_retries=max_retries
        )
        
        self.tasks[task_id] = task
        self.next_task_id += 1
        self._save_tasks()
        
        return task_id
    
    def start_task(self, task_id: str, realtime: bool = False) -> bool:
        """Start task with real-time logging"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task.status != "pending":
            return False
        
        try:
            # 1. Create tmux session
            create_cmd = f"tmux new-session -d -s {task.tmux_session}"
            result = subprocess.run(create_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                task.status = "failed"
                task.error_message = result.stderr
                self._save_tasks()
                return False
            
            # 2. Initialize log file with header
            log_file = self.logs_dir / f"{task_id}.log"
            with open(log_file, 'w', encoding='utf-8') as f:
                now = datetime.now().isoformat()
                f.write(f"[{now}] Task started: {task.name}\n")
                f.write(f"[{now}] Command: {task.command}\n")
                f.write(f"[{now}] Tmux session: {task.tmux_session}\n")
                f.write("=" * 80 + "\n")
            
            # 3. Enable real-time logging via pipe-pane
            pipe_cmd = f"tmux pipe-pane -t {task.tmux_session}:0 -o 'cat >> {log_file}'"
            subprocess.run(pipe_cmd, shell=True, capture_output=True, text=True)
            
            # 4. Send command to tmux session with email notification
            if realtime:
                # For real-time: unbuffered output
                inner = f"export PYTHONUNBUFFERED=1; stdbuf -oL -eL {task.command} 2>&1"
            else:
                # For normal: just redirect stderr to stdout
                inner = f"{task.command} 2>&1"
            
            # Add email notification and exit
            email_cmd = f"python -m task_manager.cli _send_email {task_id}"
            full_cmd = f"({inner}); {email_cmd}; exit"
            
            # Encode command as base64 to avoid quoting issues
            encoded_cmd = base64.b64encode(full_cmd.encode()).decode()
            wrapped = f"echo {encoded_cmd} | base64 -d | bash"
            send_cmd = f'tmux send-keys -t {task.tmux_session}:0 "{wrapped}" C-m'
            subprocess.run(send_cmd, shell=True, capture_output=True, text=True)
            
            # 5. Update task status
            task.status = "running"
            task.start_time = datetime.now()
            
            # Get PID from tmux session
            try:
                pid_cmd = f"tmux list-panes -t {task.tmux_session} -F '#{{pane_pid}}'"
                pid_result = subprocess.run(pid_cmd, shell=True, capture_output=True, text=True)
                if pid_result.returncode == 0:
                    task.pid = int(pid_result.stdout.strip())
            except:
                pass
            
            self._save_tasks()
            return True
            
        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
            self._save_tasks()
            return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get task status and check if completed"""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        
        # Check if running task is still active
        if task.status == "running":
            try:
                result = subprocess.run(f"tmux has-session -t {task.tmux_session}", shell=True)
                if result.returncode != 0:
                    # Session no longer exists, task completed
                    task.status = "completed"
                    task.end_time = datetime.now()
                    self._save_tasks()
                    
                    # Send completion email
                    self._send_completion_email(task)
            except:
                pass
        
        return asdict(task)
    
    def stop_task(self, task_id: str, force: bool = False) -> bool:
        """Stop task"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task.status not in ["running", "pending"]:
            return False
        
        try:
            if force:
                # Force kill tmux session
                subprocess.run(f"tmux kill-session -t {task.tmux_session}", shell=True)
            else:
                # Send Ctrl+C to tmux session
                subprocess.run(f"tmux send-keys -t {task.tmux_session} C-c", shell=True)
                time.sleep(1)
                # Check if session still exists
                result = subprocess.run(f"tmux has-session -t {task.tmux_session}", shell=True)
                if result.returncode == 0:
                    subprocess.run(f"tmux kill-session -t {task.tmux_session}", shell=True)
            
            task.status = "killed" if force else "completed"
            task.end_time = datetime.now()
            self._save_tasks()
            
            # Send completion email
            self._send_completion_email(task)
            
            return True
            
        except Exception as e:
            print(f"⚠️ Failed to stop task {task_id}: {e}")
            return False
    
    def list_tasks(self, status_filter: str = None) -> List[Dict]:
        """List tasks"""
        tasks = []
        for task in self.tasks.values():
            if status_filter is None or task.status == status_filter:
                tasks.append(asdict(task))
        
        # Sort by status (running first), then by ID (newest first)
        tasks.sort(key=lambda x: (x['status'] != 'running', -int(x['id'])))
        
        return tasks
    
    def get_tmux_output(self, task_id: str, lines: int = 50) -> str:
        """Get tmux output"""
        if task_id not in self.tasks:
            return f"Task {task_id} not found"
        
        task = self.tasks[task_id]
        
        try:
            # Try to capture from tmux pane first
            cmd = f"tmux capture-pane -t {task.tmux_session} -p"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                output = result.stdout
                if lines > 0:
                    output_lines = output.split('\n')
                    output = '\n'.join(output_lines[-lines:])
                return output
            else:
                # If tmux session is gone, read from log file
                log_file = self.logs_dir / f"{task_id}.log"
                if log_file.exists():
                    with open(log_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if lines > 0:
                            content_lines = content.split('\n')
                            content = '\n'.join(content_lines[-lines:])
                        return content
                else:
                    return f"No output available for task {task_id}"
            
        except Exception as e:
            return f"Error getting output: {e}"
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed tasks"""
        current_time = datetime.now()
        tasks_to_remove = []
        
        for task_id, task in self.tasks.items():
            if task.status in ["completed", "failed", "killed"] and task.end_time:
                age_hours = (current_time - task.end_time).total_seconds() / 3600
                if age_hours > max_age_hours:
                    tasks_to_remove.append(task_id)
        
        # Remove tasks and their log files
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
            log_file = self.logs_dir / f"{task_id}.log"
            if log_file.exists():
                log_file.unlink()
        
        if tasks_to_remove:
            print(f"🧹 Cleaned up {len(tasks_to_remove)} old tasks")
            self._save_tasks()
    
    def cleanup_task(self, task_id: str) -> bool:
        """Clean up a specific task"""
        if task_id not in self.tasks:
            return False
        
        try:
            # Remove task from memory
            del self.tasks[task_id]
            
            # Remove log file
            log_file = self.logs_dir / f"{task_id}.log"
            if log_file.exists():
                log_file.unlink()
            
            # Save updated task list
            self._save_tasks()
            return True
            
        except Exception as e:
            print(f"⚠️ Failed to cleanup task {task_id}: {e}")
            return False
    
    def _send_completion_email(self, task: Task):
        """Send task completion email if configured"""
        try:
            if task.status in ["completed", "failed", "killed"]:
                # Calculate duration
                duration = "N/A"
                if task.start_time and task.end_time:
                    duration = str(task.end_time - task.start_time).split('.')[0]
                elif task.start_time:
                    duration = str(datetime.now() - task.start_time).split('.')[0]
                
                # Format times
                start_time = task.start_time.strftime('%Y-%m-%d %H:%M:%S') if task.start_time else 'N/A'
                end_time = task.end_time.strftime('%Y-%m-%d %H:%M:%S') if task.end_time else 'N/A'
                
                # Send email with task details
                self.email_notifier.send_task_completion_email(
                    task.id, 
                    task.status, 
                    duration, 
                    start_time, 
                    end_time,
                    task.command
                )
        except Exception as e:
            print(f"⚠️ Failed to send email: {e}")