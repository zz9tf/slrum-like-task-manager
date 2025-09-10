#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Manager - 基于tmux的任务调度和监控工具

一个简单易用的任务管理系统，支持：
- 任务创建、运行、监控
- 基于tmux的会话管理
- 邮件通知
- 资源监控
- 日志管理

作者: zheng
版本: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "zheng"
__email__ = "zheng.zheng.luck@gmail.com"

from .core import TaskManager, Task
from .email import EmailNotifier
from .monitor import ResourceMonitor

__all__ = [
    "TaskManager",
    "Task", 
    "EmailNotifier",
    "ResourceMonitor",
    "__version__",
    "__author__",
    "__email__",
]
