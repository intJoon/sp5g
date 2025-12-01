import os
import psutil
import logging
import subprocess
import json
from typing import Dict, List
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)

class MonitoringManager:
    def __init__(self):
        self.metrics_history = deque(maxlen=1000)
        self.anomalies = []
        
        self.thresholds = {
            'cpu': 80,
            'memory': 85,
            'latency': 100,
            'packet_rate': 10000,
            'connections': 1000
        }
        
    def collect_metrics(self) -> Dict:
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'system': self._collect_system_metrics(),
                'network': self._collect_network_metrics(),
                'processes': self._collect_process_metrics(),
                'f1_interface': self._collect_f1_metrics()
            }
            
            self.metrics_history.append(metrics)
            
            return metrics
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {'error': str(e)}
    
    def get_current_metrics(self) -> Dict:
        if self.metrics_history:
            return self.metrics_history[-1]
        return self.collect_metrics()
    
    def get_metrics_history(self, count: int = 100) -> List[Dict]:
        return list(self.metrics_history)[-count:]
    
    def check_anomalies(self, metrics: Dict) -> bool:
        try:
            anomaly_detected = False
            
            system = metrics.get('system', {})
            network = metrics.get('network', {})
            
            if system.get('cpu_percent', 0) > self.thresholds['cpu']:
                self._log_anomaly('cpu', system['cpu_percent'], self.thresholds['cpu'])
                anomaly_detected = True
            
            if system.get('memory_percent', 0) > self.thresholds['memory']:
                self._log_anomaly('memory', system['memory_percent'], self.thresholds['memory'])
                anomaly_detected = True
            
            if network.get('packet_rate', 0) > self.thresholds['packet_rate']:
                self._log_anomaly('packet_rate', network['packet_rate'], self.thresholds['packet_rate'])
                anomaly_detected = True
            
            return anomaly_detected
        except Exception as e:
            logger.error(f"Error checking anomalies: {e}")
            return False
    
    def export_performance_data(self, format_type: str = 'csv') -> Dict:
        try:
            from config import Config
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = Config.RESULTS_DIR
            os.makedirs(output_dir, exist_ok=True)
            
            if format_type == 'csv':
                filename = f'performance_{timestamp}.csv'
                filepath = os.path.join(output_dir, filename)
                self._export_to_csv(filepath)
            elif format_type == 'json':
                filename = f'performance_{timestamp}.json'
                filepath = os.path.join(output_dir, filename)
                self._export_to_json(filepath)
            else:
                return {'status': 'error', 'message': f'Unsupported format: {format_type}'}
            
            return {
                'status': 'success',
                'message': f'Performance data exported to {filename}',
                'filepath': filepath
            }
        except Exception as e:
            logger.error(f"Error exporting performance data: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _collect_system_metrics(self) -> Dict:
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            memory = psutil.virtual_memory()
            
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'cpu_count': psutil.cpu_count(),
                'memory_percent': memory.percent,
                'memory_used_gb': memory.used / (1024**3),
                'memory_total_gb': memory.total / (1024**3),
                'disk_percent': disk.percent,
                'disk_used_gb': disk.used / (1024**3),
                'disk_total_gb': disk.total / (1024**3)
            }
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    def _collect_network_metrics(self) -> Dict:
        try:
            net_io = psutil.net_io_counters()
            
            connections = len(psutil.net_connections())
            
            packet_rate = 0
            try:
                result = subprocess.run(
                    ['sudo', 'tcpdump', '-i', 'any', '-c', '100', '-nn'],
                    capture_output=True,
                    timeout=1,
                    text=True
                )
                packet_rate = 100
            except:
                pass
            
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'connections': connections,
                'packet_rate': packet_rate
            }
        except Exception as e:
            logger.error(f"Error collecting network metrics: {e}")
            return {}
    
    def _collect_process_metrics(self) -> Dict:
        try:
            gnb_processes = []
            ue_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    if 'nr-softmodem' in pinfo['name']:
                        gnb_processes.append({
                            'pid': pinfo['pid'],
                            'name': pinfo['name'],
                            'cpu': pinfo['cpu_percent'],
                            'memory': pinfo['memory_percent']
                        })
                    elif 'nr-uesoftmodem' in pinfo['name']:
                        ue_processes.append({
                            'pid': pinfo['pid'],
                            'name': pinfo['name'],
                            'cpu': pinfo['cpu_percent'],
                            'memory': pinfo['memory_percent']
                        })
                except:
                    pass
            
            return {
                'gnb_processes': gnb_processes,
                'ue_processes': ue_processes,
                'gnb_count': len(gnb_processes),
                'ue_count': len(ue_processes)
            }
        except Exception as e:
            logger.error(f"Error collecting process metrics: {e}")
            return {}
    
    def _collect_f1_metrics(self) -> Dict:
        try:
            f1_metrics = {
                'f1c_connections': 0,
                'f1u_connections': 0,
                'latency_ms': 0,
                'throughput_mbps': 0
            }
            
            try:
                result = subprocess.run(
                    ['ss', '-tunap', 'sport = :38472 or dport = :38472'],
                    capture_output=True,
                    text=True
                )
                f1_metrics['f1c_connections'] = len(result.stdout.strip().split('\n')) - 1
            except:
                pass
            
            try:
                result = subprocess.run(
                    ['ss', '-tunap', 'sport = :2152 or dport = :2152'],
                    capture_output=True,
                    text=True
                )
                f1_metrics['f1u_connections'] = len(result.stdout.strip().split('\n')) - 1
            except:
                pass
            
            return f1_metrics
        except Exception as e:
            logger.error(f"Error collecting F1 metrics: {e}")
            return {}
    
    def _log_anomaly(self, metric_type: str, value: float, threshold: float):
        anomaly = {
            'timestamp': datetime.now().isoformat(),
            'type': metric_type,
            'value': value,
            'threshold': threshold,
            'severity': 'high' if value > threshold * 1.2 else 'medium'
        }
        
        self.anomalies.append(anomaly)
        logger.warning(f"Anomaly detected: {metric_type} = {value} (threshold: {threshold})")
    
    def _export_to_csv(self, filepath: str):
        import csv
        
        with open(filepath, 'w', newline='') as f:
            if not self.metrics_history:
                return
            
            writer = csv.writer(f)
            
            writer.writerow([
                'Timestamp', 'CPU %', 'Memory %', 'Disk %',
                'Bytes Sent', 'Bytes Recv', 'Connections', 'Packet Rate',
                'gNB Processes', 'UE Processes', 'F1-C Connections', 'F1-U Connections'
            ])
            
            for metrics in self.metrics_history:
                system = metrics.get('system', {})
                network = metrics.get('network', {})
                processes = metrics.get('processes', {})
                f1 = metrics.get('f1_interface', {})
                
                writer.writerow([
                    metrics['timestamp'],
                    system.get('cpu_percent', 0),
                    system.get('memory_percent', 0),
                    system.get('disk_percent', 0),
                    network.get('bytes_sent', 0),
                    network.get('bytes_recv', 0),
                    network.get('connections', 0),
                    network.get('packet_rate', 0),
                    processes.get('gnb_count', 0),
                    processes.get('ue_count', 0),
                    f1.get('f1c_connections', 0),
                    f1.get('f1u_connections', 0)
                ])
    
    def _export_to_json(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump(list(self.metrics_history), f, indent=2)



