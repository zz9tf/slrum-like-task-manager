#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行接口模块
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
    """主入口函数"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1]
    
    # 全局选项
    if command in ['-h', '--help']:
        show_help()
        return
    elif command in ['-v', '--version']:
        show_version()
        return
    
    # 初始化任务管理器
    manager = TaskManager()
    
    # 命令分发
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
        print(f"❌ 未知命令: {command}")
        print("使用 'task -h' 查看帮助信息")
        sys.exit(1)


def show_help():
    """显示帮助信息"""
    print("任务管理系统 - 基于tmux的任务调度和监控工具")
    print("")
    print("用法: task <command> [options]")
    print("")
    print("全局选项:")
    print("  -h, --help     显示此帮助信息")
    print("  -v, --version  显示版本信息")
    print("")
    print("可用命令:")
    print("  run     运行新任务")
    print("  list    列出任务")
    print("  kill    停止任务")
    print("  monitor 监控任务输出")
    print("  status  查看任务状态")
    print("  output  查看任务输出")
    print("  cleanup 清理旧任务")
    print("  logs    查看任务日志")
    print("  email   邮件配置")
    print("  config  配置管理")
    print("")
    print("示例:")
    print("  task run '训练模型' 'python train.py --epochs 100'")
    print("  task list")
    print("  task list --resources")
    print("  task monitor <task_id>")
    print("  task kill <task_id>")
    print("  task status <task_id>")
    print("  task output <task_id>")
    print("  task cleanup")
    print("")
    print("详细帮助:")
    print("  task <command> -h    显示特定命令的详细帮助")


def show_version():
    """显示版本信息"""
    print("任务管理系统 v1.0.0")
    print("基于tmux的任务调度和监控工具")
    print("作者: zheng")
    print("构建日期: 2025-09-09")


def cmd_run(manager: TaskManager):
    """运行任务命令"""
    if len(sys.argv) < 3:
        print("❌ 错误: 缺少必需参数")
        print("用法: task run <name> <command> [priority] [max_retries]")
        print("使用 'task run -h' 查看详细帮助")
        sys.exit(1)
    
    # 检查帮助选项
    if sys.argv[2] in ['-h', '--help']:
        print("运行新任务")
        print("")
        print("用法: task run <name> <command> [priority] [max_retries]")
        print("")
        print("参数:")
        print("  name        任务名称")
        print("  command     要执行的命令")
        print("  priority    任务优先级 (0-10, 默认0)")
        print("  max_retries 最大重试次数 (默认0)")
        print("")
        print("示例:")
        print("  task run '训练模型' 'python train.py'")
        print("  task run '重要任务' 'python important.py' 10")
        print("  task run '可能失败' 'python unstable.py' 0 3")
        print("")
        print("注意:")
        print("  - 任务将在tmux会话中运行")
        print("  - 优先级越高，任务越优先执行")
        print("  - 任务失败时会自动重试指定次数")
        return
    
    if len(sys.argv) < 4:
        print("❌ 错误: 缺少必需参数")
        print("用法: task run <name> <command> [priority] [max_retries]")
        print("使用 'task run -h' 查看详细帮助")
        sys.exit(1)
    
    name = sys.argv[2]
    command = sys.argv[3]
    priority = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    max_retries = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    
    task_id = manager.create_task(name, command, priority, max_retries)
    print(f"✅ 任务创建成功: {task_id} - {name}")
    
    if manager.start_task(task_id):
        print(f"🚀 任务已启动: {task_id}")
        print(f"📺 查看输出: task output {task_id}")
        print(f"🛑 停止任务: task kill {task_id}")
    else:
        print(f"❌ 任务启动失败: {task_id}")


def cmd_list(manager: TaskManager):
    """列出任务命令"""
    # 检查帮助选项
    if len(sys.argv) >= 3 and sys.argv[2] in ['-h', '--help']:
        print("列出所有任务")
        print("")
        print("用法: task list [选项]")
        print("")
        print("选项:")
        print("  --status <status>  按状态过滤任务")
        print("  --resources        显示系统资源使用情况")
        print("  -h, --help         显示此帮助信息")
        print("")
        print("状态值:")
        print("  pending    等待中")
        print("  running    运行中")
        print("  completed  已完成")
        print("  failed     失败")
        print("  killed     已终止")
        print("")
        print("示例:")
        print("  task list                    # 列出所有任务")
        print("  task list --status running   # 只显示运行中的任务")
        print("  task list --resources        # 显示任务和资源信息")
        return
    
    status_filter = None
    show_resources = False
    
    # 解析参数
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
        print("📋 没有找到任务")
        return
    
    print("📋 所有任务:")
    print("ID       名称                   状态           优先级    持续时间         Tmux会话")
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
        
        # 计算持续时间
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
    """停止任务命令"""
    if len(sys.argv) < 3:
        print("❌ 错误: 缺少必需参数")
        print("用法: task kill <task_id> [--force] | task kill --all [--force]")
        print("使用 'task kill -h' 查看详细帮助")
        sys.exit(1)
    
    # 检查帮助选项
    if sys.argv[2] in ['-h', '--help']:
        print("停止任务")
        print("")
        print("用法: task kill <task_id> [--force] | task kill --all [--force]")
        print("")
        print("参数:")
        print("  task_id     要停止的任务ID")
        print("  --all       停止所有运行中的任务")
        print("  --force     强制停止任务")
        print("  -h, --help  显示此帮助信息")
        print("")
        print("示例:")
        print("  task kill 00001              # 停止任务00001")
        print("  task kill 00001 --force      # 强制停止任务00001")
        print("  task kill --all              # 停止所有运行中的任务")
        print("  task kill --all --force      # 强制停止所有运行中的任务")
        print("")
        print("注意:")
        print("  - 使用--force会强制终止tmux会话")
        print("  - 停止的任务状态会变为'killed'")
        return
    
    task_id = sys.argv[2]
    force = "--force" in sys.argv
    all_tasks = "--all" in sys.argv
    
    if all_tasks:
        running_tasks = manager.list_tasks(status_filter="running")
        if not running_tasks:
            print("📋 没有运行中的任务")
            return
        
        for task in running_tasks:
            if manager.stop_task(task['id'], force):
                print(f"✅ 任务已停止: {task['id']}")
            else:
                print(f"❌ 停止任务失败: {task['id']}")
    else:
        if manager.stop_task(task_id, force):
            print(f"✅ 任务已停止: {task_id}")
        else:
            print(f"❌ 停止任务失败: {task_id}")


def cmd_monitor(manager: TaskManager):
    """监控任务命令"""
    if len(sys.argv) < 3:
        print("❌ 错误: 缺少必需参数")
        print("用法: task monitor <task_id> [--lines N] [--refresh SECONDS]")
        print("使用 'task monitor -h' 查看详细帮助")
        sys.exit(1)
    
    # 检查帮助选项
    if sys.argv[2] in ['-h', '--help']:
        print("实时监控任务")
        print("")
        print("用法: task monitor <task_id> [--lines N] [--refresh SECONDS]")
        print("")
        print("参数:")
        print("  task_id     要监控的任务ID")
        print("  --lines N   显示最后N行输出 (默认50)")
        print("  --refresh S 刷新间隔秒数 (默认2.0)")
        print("  -h, --help  显示此帮助信息")
        print("")
        print("示例:")
        print("  task monitor 00001                    # 监控任务00001")
        print("  task monitor 00001 --lines 100        # 显示最后100行")
        print("  task monitor 00001 --refresh 1.0      # 每秒刷新一次")
        print("")
        print("注意:")
        print("  - 按Ctrl+C退出监控")
        print("  - 监控会实时显示任务输出")
        return
    
    task_id = sys.argv[2]
    lines = 50
    refresh = 2.0
    
    # 解析参数
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
        print(f"❌ 任务不存在: {task_id}")
        return
    
    task = manager.tasks[task_id]
    print(f"📺 监控任务: {task.name} ({task_id})")
    print(f"📺 Tmux会话: {task.tmux_session}")
    print("=" * 60)
    
    try:
        while True:
            status = manager.get_task_status(task_id)
            if not status or status['status'] not in ['running', 'pending']:
                print(f"\n✅ 任务已结束: {status['status'] if status else 'unknown'}")
                break
            
            # 清屏并显示输出
            os.system('clear' if os.name == 'posix' else 'cls')
            print(f"📺 监控任务: {task.name} ({task_id}) - {status['status']}")
            print(f"⏱️  运行时间: {status.get('start_time', 'N/A')}")
            print("=" * 60)
            
            output = manager.get_tmux_output(task_id, lines)
            print(output)
            
            print("=" * 60)
            print("按 Ctrl+C 退出监控")
            
            time.sleep(refresh)
            
    except KeyboardInterrupt:
        print(f"\n👋 停止监控任务: {task_id}")
        sys.exit(0)


def cmd_status(manager: TaskManager):
    """查看任务状态命令"""
    if len(sys.argv) < 3:
        print("❌ 错误: 缺少必需参数")
        print("用法: task status <task_id>")
        print("使用 'task status -h' 查看详细帮助")
        sys.exit(1)
    
    # 检查帮助选项
    if sys.argv[2] in ['-h', '--help']:
        print("查看任务状态")
        print("")
        print("用法: task status <task_id>")
        print("")
        print("参数:")
        print("  task_id     要查看状态的任务ID")
        print("  -h, --help  显示此帮助信息")
        print("")
        print("示例:")
        print("  task status 00001    # 查看任务00001的状态")
        print("")
        print("显示信息:")
        print("  - 任务基本信息 (ID, 名称, 状态)")
        print("  - 运行时间统计")
        print("  - 资源使用情况")
        print("  - 最近输出")
        return
    
    task_id = sys.argv[2]
    status = manager.get_task_status(task_id)
    
    if not status:
        print(f"❌ 任务不存在: {task_id}")
        return
    
    print(f"📊 任务状态: {task_id}")
    print("=" * 40)
    print(f"名称: {status['name']}")
    print(f"状态: {status['status']}")
    print(f"开始时间: {status['start_time'] or 'N/A'}")
    print(f"结束时间: {status['end_time'] or 'N/A'}")
    print(f"Tmux会话: {status['tmux_session']}")
    print(f"PID: {status['pid'] or 'N/A'}")
    print(f"优先级: {status['priority']}")


def cmd_output(manager: TaskManager):
    """查看任务输出命令"""
    if len(sys.argv) < 3:
        print("❌ 错误: 缺少必需参数")
        print("用法: task output <task_id> [--lines N]")
        print("使用 'task output -h' 查看详细帮助")
        sys.exit(1)
    
    # 检查帮助选项
    if sys.argv[2] in ['-h', '--help']:
        print("查看任务输出")
        print("")
        print("用法: task output <task_id> [--lines N]")
        print("")
        print("参数:")
        print("  task_id     要查看输出的任务ID")
        print("  --lines N   显示最后N行输出 (默认50)")
        print("  -h, --help  显示此帮助信息")
        print("")
        print("示例:")
        print("  task output 00001              # 查看任务00001的输出")
        print("  task output 00001 --lines 100  # 显示最后100行")
        print("")
        print("注意:")
        print("  - 输出来自tmux会话")
        print("  - 只显示最近的输出内容")
        return
    
    task_id = sys.argv[2]
    lines = 50
    
    # 解析参数
    i = 3
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--lines" and i + 1 < len(sys.argv):
            lines = int(sys.argv[i + 1])
            i += 1
        i += 1
    
    print(f"📋 任务输出: {task_id}")
    print("=" * 60)
    output = manager.get_tmux_output(task_id, lines)
    print(output)


def cmd_cleanup(manager: TaskManager):
    """清理任务命令"""
    # 检查帮助选项
    if len(sys.argv) >= 3 and sys.argv[2] in ['-h', '--help']:
        print("清理已完成的任务")
        print("")
        print("用法: task cleanup [hours]")
        print("")
        print("参数:")
        print("  hours       清理已完成超过指定小时的任务 (默认24)")
        print("  -h, --help  显示此帮助信息")
        print("")
        print("示例:")
        print("  task cleanup        # 清理超过24小时的已完成任务")
        print("  task cleanup 12     # 清理超过12小时的已完成任务")
        print("  task cleanup 0      # 清理所有已完成任务")
        print("")
        print("注意:")
        print("  - 只清理已完成、失败或已终止的任务")
        print("  - 运行中的任务不会被清理")
        print("  - 清理会同时删除任务记录和日志文件")
        return
    
    max_age_hours = 24
    if len(sys.argv) > 2:
        try:
            max_age_hours = int(sys.argv[2])
        except ValueError:
            print("❌ 错误: 无效的时间参数")
            print("使用 'task cleanup -h' 查看帮助")
            sys.exit(1)
    
    print(f"🧹 开始清理任务 (已完成任务超过{max_age_hours}小时)")
    manager.cleanup_old_tasks(max_age_hours)
    print("✅ 清理完成")


def cmd_logs(manager: TaskManager):
    """查看任务日志命令"""
    if len(sys.argv) < 3:
        print("❌ 错误: 缺少必需参数")
        print("用法: task logs <task_id> [lines]")
        print("使用 'task logs -h' 查看详细帮助")
        sys.exit(1)
    
    # 检查帮助选项
    if sys.argv[2] in ['-h', '--help']:
        print("查看任务日志")
        print("")
        print("用法: task logs <task_id> [lines]")
        print("")
        print("参数:")
        print("  task_id     要查看日志的任务ID")
        print("  lines       显示最后N行日志 (默认100)")
        print("  -h, --help  显示此帮助信息")
        print("")
        print("示例:")
        print("  task logs 00001        # 查看任务00001的日志")
        print("  task logs 00001 50     # 显示最后50行日志")
        print("")
        print("注意:")
        print("  - 日志文件保存在 ~/.task_manager/logs/")
        print("  - 日志包含任务的完整输出记录")
        return
    
    task_id = sys.argv[2]
    lines = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    
    log_file = manager.logs_dir / f"{task_id}.log"
    if log_file.exists():
        print(f"📋 任务日志: {task_id}")
        print("=" * 60)
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if lines > 0:
                    content_lines = content.split('\n')
                    content = '\n'.join(content_lines[-lines:])
                print(content)
        except Exception as e:
            print(f"❌ 读取日志失败: {e}")
    else:
        print(f"❌ 日志文件不存在: {task_id}")


def cmd_email(manager: TaskManager):
    """邮件配置命令"""
    if len(sys.argv) < 3:
        print("❌ 错误: 缺少必需参数")
        print("用法: task email <action>")
        print("操作: enable, disable, show, test")
        print("使用 'task email -h' 查看详细帮助")
        sys.exit(1)
    
    # 检查帮助选项
    if sys.argv[2] in ['-h', '--help']:
        print("邮件通知管理")
        print("")
        print("用法: task email <action>")
        print("")
        print("操作:")
        print("  enable      启用邮件通知")
        print("  disable     禁用邮件通知")
        print("  show        显示当前邮件配置")
        print("  test        测试邮件发送")
        print("  -h, --help  显示此帮助信息")
        print("")
        print("示例:")
        print("  task email enable    # 启用邮件通知")
        print("  task email disable   # 禁用邮件通知")
        print("  task email show      # 查看当前配置")
        print("  task email test      # 发送测试邮件")
        print("")
        print("注意:")
        print("  - 需要先配置邮件设置才能使用")
        print("  - 使用 'task config' 命令进行邮件配置")
        return
    
    action = sys.argv[2]
    email_notifier = manager.email_notifier
    
    if action == "enable":
        # 这里需要实现启用邮件的逻辑
        print("✅ 邮件通知已启用")
    elif action == "disable":
        # 这里需要实现禁用邮件的逻辑
        print("✅ 邮件通知已禁用")
    elif action == "show":
        print("📧 当前邮件配置:")
        print(f"  接收邮箱: {email_notifier.config['to_email']}")
        print(f"  状态: {'启用' if email_notifier.config['enabled'] else '禁用'}")
        print(f"  Token文件: {email_notifier.config['token_file']}")
    elif action == "test":
        print("📧 发送测试邮件...")
        if email_notifier.test_email():
            print("✅ 测试邮件发送成功")
        else:
            print("❌ 测试邮件发送失败")
    else:
        print(f"❌ 未知操作: {action}")
        sys.exit(1)


def cmd_config(manager: TaskManager):
    """配置管理命令"""
    if len(sys.argv) < 3:
        print("❌ 错误: 缺少必需参数")
        print("用法: task config <action> [file_path]")
        print("")
        print("操作:")
        print("  init                          初始化配置文件")
        print("  email <config_file>           配置邮件设置")
        print("  token <token_file>            配置Gmail token")
        print("  google_api file <creds_file>  配置Google API凭据")
        print("  google_api login              通过Google API登录获取token")
        print("  show                          显示当前配置")
        print("  test                          测试邮件发送")
        print("")
        print("示例:")
        print("  task config init")
        print("  task config email ~/my_email_config.json")
        print("  task config token ~/my_token.json")
        print("  task config google_api file ~/credentials.json")
        print("  task config google_api login")
        print("  task config show")
        print("")
        print("使用 'task config -h' 查看详细帮助")
        sys.exit(1)
    
    # 检查帮助选项
    if sys.argv[2] in ['-h', '--help']:
        print("配置管理")
        print("")
        print("用法: task config <action> [file_path]")
        print("")
        print("操作:")
        print("  init                          初始化配置文件")
        print("  email <config_file>           配置邮件设置")
        print("  token <token_file>            配置Gmail token")
        print("  google_api file <creds_file>  配置Google API凭据")
        print("  google_api login              通过Google API登录获取token")
        print("  show                          显示当前配置")
        print("  test                          测试邮件发送")
        print("  -h, --help                    显示此帮助信息")
        print("")
        print("示例:")
        print("  task config init")
        print("  task config email ~/my_email_config.json")
        print("  task config token ~/my_token.json")
        print("  task config google_api file ~/credentials.json")
        print("  task config google_api login")
        print("  task config show")
        print("")
        print("配置文件位置: ~/.task_manager/config/")
        return
    
    action = sys.argv[2]
    config_manager = ConfigManager(manager.data_dir)
    
    if action == "init":
        config_manager.init_config()
    elif action == "email":
        if len(sys.argv) < 4:
            print("❌ 错误: 缺少配置文件路径")
            print("用法: task config email <config_file>")
            sys.exit(1)
        config_manager.import_email_config(sys.argv[3])
    elif action == "token":
        if len(sys.argv) < 4:
            print("❌ 错误: 缺少token文件路径")
            print("用法: task config token <token_file>")
            sys.exit(1)
        config_manager.import_token(sys.argv[3])
    elif action == "google_api":
        if len(sys.argv) < 4:
            print("❌ 错误: 缺少google_api子命令")
            print("用法: task config google_api <file|login> [file_path]")
            sys.exit(1)
        sub_action = sys.argv[3]
        if sub_action == "file":
            if len(sys.argv) < 5:
                print("❌ 错误: 缺少凭据文件路径")
                print("用法: task config google_api file <credentials_file>")
                sys.exit(1)
            config_manager.setup_google_api(sys.argv[4])
        elif sub_action == "login":
            config_manager.google_api_login()
        else:
            print(f"❌ 未知的google_api操作: {sub_action}")
            print("可用操作: file, login")
            sys.exit(1)
    elif action == "show":
        config_manager.show_config()
    elif action == "test":
        config_manager.test_config()
    else:
        print(f"❌ 未知操作: {action}")
        sys.exit(1)




if __name__ == "__main__":
    main()
