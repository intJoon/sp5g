#!/usr/bin/env python3

import json
import logging
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque

logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    def __init__(self):
        self.attack_metrics = deque(maxlen=1000)
        self.defense_metrics = deque(maxlen=1000)
        self.baseline_metrics = deque(maxlen=100)
        
    def record_baseline(self):
        metrics = self._collect_current_metrics()
        metrics['type'] = 'baseline'
        self.baseline_metrics.append(metrics)
        logger.info("Baseline metrics recorded")
        return metrics
    
    def record_attack_impact(self, attack_type: str, attack_start_time: datetime):
        current_metrics = self._collect_current_metrics()
        current_metrics['type'] = 'attack'
        current_metrics['attack_type'] = attack_type
        current_metrics['attack_duration'] = (datetime.now() - attack_start_time).total_seconds()
        
        baseline = self._get_baseline()
        if baseline:
            current_metrics['cpu_delta'] = current_metrics['cpu_percent'] - baseline['cpu_percent']
            current_metrics['memory_delta'] = current_metrics['memory_percent'] - baseline['memory_percent']
            current_metrics['latency_delta'] = current_metrics['f1_latency_ms'] - baseline['f1_latency_ms']
            current_metrics['availability_delta'] = current_metrics['service_availability'] - baseline['service_availability']
        
        self.attack_metrics.append(current_metrics)
        logger.debug(f"Attack impact recorded: {attack_type}")
        return current_metrics
    
    def record_defense_effectiveness(self, defense_type: str, detection_time: datetime, 
                                    response_time: Optional[datetime] = None):
        current_metrics = self._collect_current_metrics()
        current_metrics['type'] = 'defense'
        current_metrics['defense_type'] = defense_type
        current_metrics['detection_time'] = detection_time.isoformat()
        
        if response_time:
            current_metrics['response_time_seconds'] = (response_time - detection_time).total_seconds()
        
        baseline = self._get_baseline()
        if baseline:
            current_metrics['recovery_cpu'] = baseline['cpu_percent'] - current_metrics['cpu_percent']
            current_metrics['recovery_memory'] = baseline['memory_percent'] - current_metrics['memory_percent']
            current_metrics['recovery_availability'] = current_metrics['service_availability'] - baseline['service_availability']
        
        self.defense_metrics.append(current_metrics)
        logger.debug(f"Defense effectiveness recorded: {defense_type}")
        return current_metrics
    
    def _collect_current_metrics(self) -> Dict:
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            connections = len(psutil.net_connections())
            net_io = psutil.net_io_counters()
            
            f1_latency = self._estimate_f1_latency()
            service_availability = self._estimate_service_availability()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'connections': connections,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'f1_latency_ms': f1_latency,
                'service_availability': service_availability
            }
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _estimate_f1_latency(self) -> float:
        try:
            import subprocess
            result = subprocess.run(['ping', '-c', '1', '-W', '1', '192.168.71.130'], 
                                  capture_output=True, timeout=2)
            if result.returncode == 0:
                output = result.stdout.decode()
                if 'time=' in output:
                    latency_str = output.split('time=')[1].split(' ')[0]
                    return float(latency_str)
        except:
            pass
        return 0.0
    
    def _estimate_service_availability(self) -> float:
        try:
            import subprocess
            result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}'], 
                                  capture_output=True, timeout=2)
            if result.returncode == 0:
                containers = result.stdout.decode().strip().split('\n')
                expected_containers = ['oai-amf', 'oai-smf', 'oai-upf', 'oai-cucp', 'oai-cuup', 'oai-du']
                running = sum(1 for c in expected_containers if any(c in name for name in containers))
                return (running / len(expected_containers)) * 100.0
        except:
            pass
        return 100.0
    
    def _get_baseline(self) -> Optional[Dict]:
        if self.baseline_metrics:
            return self.baseline_metrics[-1]
        return None
    
    def get_attack_effect_summary(self) -> Dict:
        if not self.attack_metrics:
            return {'error': 'No attack metrics recorded'}
        
        attack_data = [m for m in self.attack_metrics if m.get('type') == 'attack']
        if not attack_data:
            return {'error': 'No attack data available'}
        
        cpu_deltas = [m.get('cpu_delta', 0) for m in attack_data if 'cpu_delta' in m]
        memory_deltas = [m.get('memory_delta', 0) for m in attack_data if 'memory_delta' in m]
        latency_deltas = [m.get('latency_delta', 0) for m in attack_data if 'latency_delta' in m]
        availability_deltas = [m.get('availability_delta', 0) for m in attack_data if 'availability_delta' in m]
        
        return {
            'cpu_impact': {
                'max_increase': max(cpu_deltas) if cpu_deltas else 0,
                'avg_increase': sum(cpu_deltas) / len(cpu_deltas) if cpu_deltas else 0
            },
            'memory_impact': {
                'max_increase': max(memory_deltas) if memory_deltas else 0,
                'avg_increase': sum(memory_deltas) / len(memory_deltas) if memory_deltas else 0
            },
            'latency_impact': {
                'max_increase_ms': max(latency_deltas) if latency_deltas else 0,
                'avg_increase_ms': sum(latency_deltas) / len(latency_deltas) if latency_deltas else 0
            },
            'availability_impact': {
                'max_decrease': min(availability_deltas) if availability_deltas else 0,
                'avg_decrease': sum(availability_deltas) / len(availability_deltas) if availability_deltas else 0
            },
            'total_attacks': len(attack_data)
        }
    
    def get_defense_effect_summary(self) -> Dict:
        if not self.defense_metrics:
            return {'error': 'No defense metrics recorded'}
        
        defense_data = [m for m in self.defense_metrics if m.get('type') == 'defense']
        if not defense_data:
            return {'error': 'No defense data available'}
        
        response_times = [m.get('response_time_seconds', 0) for m in defense_data if 'response_time_seconds' in m]
        recovery_cpus = [m.get('recovery_cpu', 0) for m in defense_data if 'recovery_cpu' in m]
        recovery_availabilities = [m.get('recovery_availability', 0) for m in defense_data if 'recovery_availability' in m]
        
        return {
            'detection_accuracy': {
                'total_detections': len(defense_data),
                'avg_response_time_seconds': sum(response_times) / len(response_times) if response_times else 0
            },
            'recovery_effectiveness': {
                'avg_cpu_recovery': sum(recovery_cpus) / len(recovery_cpus) if recovery_cpus else 0,
                'avg_availability_recovery': sum(recovery_availabilities) / len(recovery_availabilities) if recovery_availabilities else 0
            },
            'total_defenses': len(defense_data)
        }
    
    def export_report(self, filepath: str):
        report = {
            'timestamp': datetime.now().isoformat(),
            'baseline': list(self.baseline_metrics),
            'attack_effect': self.get_attack_effect_summary(),
            'defense_effect': self.get_defense_effect_summary(),
            'attack_metrics': list(self.attack_metrics)[-100:],
            'defense_metrics': list(self.defense_metrics)[-100:]
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Performance report exported to {filepath}")

