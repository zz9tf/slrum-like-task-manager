#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源监控模块
"""

import psutil
import subprocess
from typing import Dict, Any, Optional


class ResourceMonitor:
    """系统资源监控器"""
    
    def __init__(self):
        pass
    
    def get_system_resources(self) -> Dict[str, Any]:
        """获取系统资源信息"""
        try:
            # CPU信息
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # 内存信息
            memory = psutil.virtual_memory()
            memory_info = {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used,
                'free': memory.free
            }
            
            # 磁盘信息
            disk = psutil.disk_usage('/')
            disk_info = {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': (disk.used / disk.total) * 100
            }
            
            # GPU信息
            gpu_info = self._get_gpu_info()
            
            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count
                },
                'memory': memory_info,
                'disk': disk_info,
                'gpu': gpu_info
            }
        except Exception as e:
            return {'error': f'获取系统资源失败: {e}'}
    
    def _get_gpu_info(self) -> Dict[str, Any]:
        """获取GPU信息"""
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,utilization.gpu', 
                                   '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                gpus = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 4:
                            gpus.append({
                                'name': parts[0],
                                'memory_total': int(parts[1]) if parts[1].isdigit() else 0,
                                'memory_used': int(parts[2]) if parts[2].isdigit() else 0,
                                'utilization': int(parts[3]) if parts[3].isdigit() else 0
                            })
                
                return {
                    'status': 'available',
                    'gpus': gpus
                }
            else:
                return {
                    'status': 'unavailable',
                    'gpus': []
                }
        except Exception:
            return {
                'status': 'unavailable',
                'gpus': []
            }
    
    def format_resources(self, resources: Dict[str, Any]) -> str:
        """格式化资源信息为可读字符串"""
        if 'error' in resources:
            return f"❌ {resources['error']}"
        
        lines = []
        
        # CPU信息
        cpu = resources.get('cpu', {})
        lines.append(f"🖥️  CPU: {cpu.get('percent', 0):.1f}% ({cpu.get('count', 0)} 核心)")
        
        # 内存信息
        memory = resources.get('memory', {})
        memory_gb = memory.get('total', 0) / (1024**3)
        memory_used_gb = memory.get('used', 0) / (1024**3)
        lines.append(f"💾 内存: {memory_used_gb:.1f}GB / {memory_gb:.1f}GB ({memory.get('percent', 0):.1f}%)")
        
        # 磁盘信息
        disk = resources.get('disk', {})
        disk_gb = disk.get('total', 0) / (1024**3)
        disk_used_gb = disk.get('used', 0) / (1024**3)
        lines.append(f"💿 磁盘: {disk_used_gb:.1f}GB / {disk_gb:.1f}GB ({disk.get('percent', 0):.1f}%)")
        
        # GPU信息
        gpu = resources.get('gpu', {})
        if gpu.get('status') == 'available' and gpu.get('gpus'):
            for i, gpu_info in enumerate(gpu['gpus']):
                memory_total = gpu_info.get('memory_total', 0)
                memory_used = gpu_info.get('memory_used', 0)
                utilization = gpu_info.get('utilization', 0)
                lines.append(f"🎮 GPU{i}: {gpu_info.get('name', 'Unknown')} - {memory_used}MB/{memory_total}MB ({utilization}%)")
        else:
            lines.append("🎮 GPU: 不可用")
        
        return "\n".join(lines)
