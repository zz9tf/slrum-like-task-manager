#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resource Monitoring Module
"""

import psutil
import subprocess
from typing import Dict, Any, Optional


class ResourceMonitor:
    """System Resource Monitor"""
    
    def __init__(self):
        pass
    
    def get_system_resources(self) -> Dict[str, Any]:
        """Get system resource information"""
        try:
            # CPU information
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory information
            memory = psutil.virtual_memory()
            memory_info = {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used,
                'free': memory.free
            }
            
            # Disk information
            disk = psutil.disk_usage('/')
            disk_info = {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': (disk.used / disk.total) * 100
            }
            
            # GPU information (if available)
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
            print(f"⚠️ Failed to get system resources: {e}")
            return {}
    
    def _get_gpu_info(self) -> Optional[Dict[str, Any]]:
        """Get GPU information"""
        try:
            # Try to get NVIDIA GPU info
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,utilization.gpu', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                gpus = []
                
                for line in lines:
                    if line.strip():
                        parts = line.split(', ')
                        if len(parts) >= 4:
                            gpus.append({
                                'name': parts[0],
                                'memory_total': int(parts[1]),
                                'memory_used': int(parts[2]),
                                'utilization': int(parts[3])
                            })
                
                return {
                    'available': True,
                    'gpus': gpus
                }
            else:
                return {'available': False, 'reason': 'nvidia-smi not available'}
                
        except subprocess.TimeoutExpired:
            return {'available': False, 'reason': 'nvidia-smi timeout'}
        except FileNotFoundError:
            return {'available': False, 'reason': 'nvidia-smi not found'}
        except Exception as e:
            return {'available': False, 'reason': str(e)}
    
    def format_resources(self, resources: Dict[str, Any]) -> str:
        """Format resource information for display"""
        if not resources:
            return "❌ Unable to get resource information"
        
        output = []
        output.append("🖥️  System Resources:")
        output.append("=" * 60)
        
        # CPU
        cpu = resources.get('cpu', {})
        output.append(f"CPU: {cpu.get('percent', 0):.1f}% ({cpu.get('count', 0)} cores)")
        
        # Memory
        memory = resources.get('memory', {})
        memory_total_gb = memory.get('total', 0) / (1024**3)
        memory_used_gb = memory.get('used', 0) / (1024**3)
        memory_percent = memory.get('percent', 0)
        output.append(f"Memory: {memory_used_gb:.1f}GB / {memory_total_gb:.1f}GB ({memory_percent:.1f}%)")
        
        # Disk
        disk = resources.get('disk', {})
        disk_total_gb = disk.get('total', 0) / (1024**3)
        disk_used_gb = disk.get('used', 0) / (1024**3)
        disk_percent = disk.get('percent', 0)
        output.append(f"Disk: {disk_used_gb:.1f}GB / {disk_total_gb:.1f}GB ({disk_percent:.1f}%)")
        
        # GPU
        gpu = resources.get('gpu', {})
        if gpu.get('available', False):
            gpus = gpu.get('gpus', [])
            for i, gpu_info in enumerate(gpus):
                name = gpu_info.get('name', f'GPU {i}')
                memory_used = gpu_info.get('memory_used', 0)
                memory_total = gpu_info.get('memory_total', 0)
                utilization = gpu_info.get('utilization', 0)
                output.append(f"GPU {i}: {name} - {memory_used}MB / {memory_total}MB ({utilization}%)")
        else:
            output.append(f"GPU: Not available ({gpu.get('reason', 'Unknown')})")
        
        return '\n'.join(output)
    
    def get_task_resources(self, task_id: str) -> Dict[str, Any]:
        """Get resource usage for specific task"""
        try:
            # This would need to be implemented based on specific requirements
            # For now, return basic system resources
            return self.get_system_resources()
        except Exception as e:
            print(f"⚠️ Failed to get task resources: {e}")
            return {}

