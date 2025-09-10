#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Manager Core Module
"""

import os
import json
import uuid
import time
import subprocess
import psutil
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

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
    """Task Manager"""
    
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
                    for time_field in ['created_time', 'start_time', 'end_time', 'pid']:
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
                for time_field in ['created_time', 'start_time', 'end_time', 'pid']:
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
    
    def start_task(self, task_id: str) -> bool:
        """Start task"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task.status != "pending":
            return False
        
        try:
            # Create tmux session
            cmd = f"tmux new-session -d -s {task.tmux_session} '{task.command}'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                task.status = "failed"
                task.error_message = result.stderr
                self._save_tasks()
                return False
            
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
            
            # Send email notification
            self._send_task_completion_email(task)
            
            return True
            
        except Exception as e:
            print(f"⚠️ Failed to stop task {task_id}: {e}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get task status"""
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
                    
                    # Send email notification
                    self._send_task_completion_email(task)
            except:
                pass
        
        return asdict(task)
    
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
            # Capture tmux pane content
            cmd = f"tmux capture-pane -t {task.tmux_session} -p"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                return f"Failed to get output: {result.stderr}"
            
            output = result.stdout
            if lines > 0:
                output_lines = output.split('\n')
                output = '\n'.join(output_lines[-lines:])
            
            # Save to log file
            self._save_task_log(task_id, output)
            
            return output
            
        except Exception as e:
            return f"Error getting output: {e}"
    
    def _save_task_log(self, task_id: str, output: str):
        """Save task log to file"""
        try:
            log_file = self.logs_dir / f"{task_id}.log"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().isoformat()}] {output}\n")
        except Exception as e:
            print(f"⚠️ Failed to save log: {e}")
    
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
    
    def _send_task_completion_email(self, task: Task):
        """Send task completion email"""
        try:
            if task.status in ["completed", "failed", "killed"]:
                self.email_notifier.send_task_completion_email(task)
        except Exception as e:
            print(f"⚠️ Failed to send email: {e}")
