#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理器核心模块
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
    """任务数据结构"""
    id: str
    name: str
    command: str
    tmux_session: str
    status: str = "pending"
    priority: int = 0
    max_retries: int = 0
    created_at: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    pid: Optional[int] = None
    retry_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class TaskManager:
    """任务管理器核心类"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # 使用用户主目录下的配置
            self.data_dir = Path.home() / ".task_manager"
        else:
            self.data_dir = Path(data_dir)
            
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_file = self.data_dir / "tasks.json"
        self.logs_dir = self.data_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.tasks = self.load_tasks()
        self.email_notifier = EmailNotifier(self.data_dir)
        self.resource_monitor = ResourceMonitor()
    
    def load_tasks(self) -> Dict[str, Task]:
        """加载任务"""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                tasks = {}
                for task_id, task_data in data.items():
                    # 转换datetime字符串
                    for time_field in ['created_at', 'start_time', 'end_time']:
                        if task_data.get(time_field):
                            task_data[time_field] = datetime.fromisoformat(task_data[time_field])
                    tasks[task_id] = Task(**task_data)
                return tasks
            except Exception as e:
                print(f"⚠️ 加载任务失败: {e}")
        return {}
    
    def save_tasks(self):
        """保存任务"""
        try:
            data = {}
            for task_id, task in self.tasks.items():
                task_dict = asdict(task)
                # 转换datetime为字符串
                for time_field in ['created_at', 'start_time', 'end_time']:
                    if task_dict.get(time_field):
                        task_dict[time_field] = task_dict[time_field].isoformat()
                data[task_id] = task_dict
            
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ 保存任务失败: {e}")
    
    def create_task(self, name: str, command: str, priority: int = 0, max_retries: int = 0) -> str:
        """创建新任务"""
        task_id = self._get_next_task_id()
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
        self.save_tasks()
        return task_id
    
    def _get_next_task_id(self, max_id: int = 99999) -> str:
        """获取下一个任务ID"""
        if not self.tasks:
            return "00001"
        
        existing_ids = []
        for task_id in self.tasks.keys():
            try:
                existing_ids.append(int(task_id))
            except ValueError:
                continue
        
        if not existing_ids:
            return "00001"
        
        max_existing_id = max(existing_ids)
        if max_existing_id >= max_id:
            # 寻找可用的ID
            for i in range(1, max_id + 1):
                if i not in existing_ids:
                    return f"{i:05d}"
            return f"{max_existing_id + 1:05d}"
        else:
            return f"{max_existing_id + 1:05d}"
    
    def start_task(self, task_id: str) -> bool:
        """启动任务"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task.status != "pending":
            return False
        
        try:
            # 创建tmux会话
            tmux_cmd = f"tmux new-session -d -s {task.tmux_session} '{task.command}'"
            result = subprocess.run(tmux_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                task.status = "running"
                task.start_time = datetime.now()
                task.pid = self._get_tmux_pid(task.tmux_session)
                self.save_tasks()
                return True
            return False
        except Exception:
            return False
    
    def stop_task(self, task_id: str, force: bool = False) -> bool:
        """停止任务"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task.status not in ["running", "pending"]:
            return False
        
        try:
            if force:
                subprocess.run(['tmux', 'kill-session', '-t', task.tmux_session], 
                             capture_output=True)
            else:
                subprocess.run(['tmux', 'send-keys', '-t', task.tmux_session, 'C-c'], 
                             capture_output=True)
                time.sleep(2)
                subprocess.run(['tmux', 'kill-session', '-t', task.tmux_session], 
                             capture_output=True)
            
            task.status = "killed" if force else "completed"
            task.end_time = datetime.now()
            self.save_tasks()
            
            # 发送邮件通知
            self.email_notifier.send_task_completion_email(task_id, task.status)
            
            return True
        except Exception:
            return False
    
    def get_task_status(self, task_id: str, cleanup: bool = True) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        if task_id not in self.tasks:
            return None
        
        # 自动清理旧任务
        if cleanup:
            self.cleanup_old_tasks()
        
        task = self.tasks[task_id]
        
        # 检查tmux会话是否还在运行
        if task.status == "running":
            try:
                result = subprocess.run(['tmux', 'has-session', '-t', task.tmux_session], 
                                     capture_output=True)
                if result.returncode != 0:
                    task.status = "completed"
                    task.end_time = datetime.now()
                    self.save_tasks()
                    
                    # 发送邮件通知
                    self.email_notifier.send_task_completion_email(task_id, task.status)
            except Exception:
                pass
        
        return {
            'id': task.id,
            'name': task.name,
            'status': task.status,
            'start_time': task.start_time,
            'end_time': task.end_time,
            'tmux_session': task.tmux_session,
            'pid': task.pid,
            'priority': task.priority
        }
    
    def list_tasks(self, status_filter: str = None, cleanup: bool = True) -> List[Dict[str, Any]]:
        """列出任务"""
        # 自动清理旧任务
        if cleanup:
            self.cleanup_old_tasks()
        
        task_list = []
        for task in self.tasks.values():
            if status_filter and task.status != status_filter:
                continue
            
            status_info = self.get_task_status(task.id, cleanup=False)
            if status_info:
                task_list.append(status_info)
        
        # 先按状态排序（running优先），再按ID排序（最新的在上面）
        def sort_key(x):
            status_priority = 0 if x['status'] == 'running' else 1
            task_id = int(x['id']) if x['id'].isdigit() else 0
            return (status_priority, -task_id)  # 负号让ID大的在上面
        
        task_list.sort(key=sort_key)
        return task_list
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """清理旧任务"""
        current_time = datetime.now()
        tasks_to_remove = []
        
        for task_id, task in self.tasks.items():
            if task.status in ['completed', 'failed', 'killed']:
                end_time = task.end_time or task.start_time
                if end_time:
                    age_hours = (current_time - end_time).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        tasks_to_remove.append(task_id)
        
        # 删除旧任务
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        # 清理对应的日志文件
        logs_removed = 0
        for task_id in tasks_to_remove:
            log_file = self.logs_dir / f"{task_id}.log"
            if log_file.exists():
                try:
                    log_file.unlink()
                    logs_removed += 1
                except Exception as e:
                    print(f"⚠️ 删除日志文件失败 {task_id}: {e}")
        
        if tasks_to_remove:
            self.save_tasks()
            print(f"🧹 已清理 {len(tasks_to_remove)} 个已完成的任务")
            if logs_removed > 0:
                print(f"📝 已清理 {logs_removed} 个对应的日志文件")
    
    def get_tmux_output(self, task_id: str, lines: int = 50) -> str:
        """获取tmux输出"""
        if task_id not in self.tasks:
            return "任务不存在"
        
        task = self.tasks[task_id]
        try:
            result = subprocess.run(['tmux', 'capture-pane', '-t', task.tmux_session, 
                                   '-p', '-S', f'-{lines}'], 
                                  capture_output=True, text=True)
            output = result.stdout if result.returncode == 0 else "无法获取输出"
            
            # 保存输出到日志文件
            self._save_task_log(task_id, output)
            return output
        except Exception as e:
            error_msg = f"获取输出失败: {e}"
            self._save_task_log(task_id, error_msg)
            return error_msg
    
    def _save_task_log(self, task_id: str, content: str):
        """保存任务日志到文件"""
        try:
            log_file = self.logs_dir / f"{task_id}.log"
            with open(log_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"\n[{timestamp}] 任务输出:\n")
                f.write(content)
                f.write("\n" + "="*60 + "\n")
        except Exception as e:
            print(f"⚠️ 保存日志失败: {e}")
    
    def _get_tmux_pid(self, session_name: str) -> Optional[int]:
        """获取tmux会话PID"""
        try:
            result = subprocess.run(['tmux', 'list-sessions', '-F', '#{session_name}:#{session_pid}'], 
                                  capture_output=True, text=True)
            for line in result.stdout.strip().split('\n'):
                if line.startswith(f"{session_name}:"):
                    return int(line.split(':')[1])
        except Exception:
            pass
        return None
