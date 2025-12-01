#!/usr/bin/env python3

import argparse
import sys
import time
import logging
import psutil
import subprocess
from collections import deque
from datetime import datetime
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AttackDetector:
    def __init__(self, cpu_threshold=80, memory_threshold=85, 
                 packet_threshold=10000, connection_threshold=1000):
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.packet_threshold = packet_threshold
        self.connection_threshold = connection_threshold
        
        self.cpu_history = deque(maxlen=60)
        self.memory_history = deque(maxlen=60)
        self.packet_history = deque(maxlen=60)
        self.connection_history = deque(maxlen=60)
        
        self.anomaly_log = []
        self.detection_active = True
        
        logger.info("Attack Detector initialized")
        logger.info(f"Thresholds - CPU: {cpu_threshold}%, Memory: {memory_threshold}%, "
                   f"Packets: {packet_threshold}/sec, Connections: {connection_threshold}")
    
    def collect_metrics(self):
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory_percent = psutil.virtual_memory().percent
        
        connections = len(psutil.net_connections())
        
        packet_rate = self._estimate_packet_rate()
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'connections': connections,
            'packet_rate': packet_rate
        }
        
        self.cpu_history.append(cpu_percent)
        self.memory_history.append(memory_percent)
        self.connection_history.append(connections)
        self.packet_history.append(packet_rate)
        
        return metrics
    
    def _estimate_packet_rate(self):
        try:
            net_io_start = psutil.net_io_counters()
            time.sleep(0.1)
            net_io_end = psutil.net_io_counters()
            
            packets_sent_rate = (net_io_end.packets_sent - net_io_start.packets_sent) * 10
            packets_recv_rate = (net_io_end.packets_recv - net_io_start.packets_recv) * 10
            
            return packets_sent_rate + packets_recv_rate
        except:
            return 0
    
    def threshold_based_detection(self, metrics):
        anomalies = []
        
        if metrics['cpu_percent'] > self.cpu_threshold:
            anomalies.append({
                'type': 'cpu_overload',
                'severity': 'high' if metrics['cpu_percent'] > self.cpu_threshold * 1.2 else 'medium',
                'value': metrics['cpu_percent'],
                'threshold': self.cpu_threshold,
                'message': f"CPU usage ({metrics['cpu_percent']:.1f}%) exceeds threshold ({self.cpu_threshold}%)"
            })
        
        if metrics['memory_percent'] > self.memory_threshold:
            anomalies.append({
                'type': 'memory_overload',
                'severity': 'high' if metrics['memory_percent'] > self.memory_threshold * 1.2 else 'medium',
                'value': metrics['memory_percent'],
                'threshold': self.memory_threshold,
                'message': f"Memory usage ({metrics['memory_percent']:.1f}%) exceeds threshold ({self.memory_threshold}%)"
            })
        
        if metrics['packet_rate'] > self.packet_threshold:
            anomalies.append({
                'type': 'packet_flood',
                'severity': 'critical' if metrics['packet_rate'] > self.packet_threshold * 2 else 'high',
                'value': metrics['packet_rate'],
                'threshold': self.packet_threshold,
                'message': f"Packet rate ({metrics['packet_rate']:.0f} pps) exceeds threshold ({self.packet_threshold} pps)"
            })
        
        if metrics['connections'] > self.connection_threshold:
            anomalies.append({
                'type': 'connection_flood',
                'severity': 'high',
                'value': metrics['connections'],
                'threshold': self.connection_threshold,
                'message': f"Connection count ({metrics['connections']}) exceeds threshold ({self.connection_threshold})"
            })
        
        return anomalies
    
    def statistical_analysis(self, metrics):
        anomalies = []
        
        if len(self.cpu_history) >= 10:
            avg_cpu = sum(self.cpu_history) / len(self.cpu_history)
            std_cpu = (sum((x - avg_cpu) ** 2 for x in self.cpu_history) / len(self.cpu_history)) ** 0.5
            
            if metrics['cpu_percent'] > avg_cpu + 2 * std_cpu:
                anomalies.append({
                    'type': 'cpu_spike',
                    'severity': 'medium',
                    'value': metrics['cpu_percent'],
                    'baseline': avg_cpu,
                    'message': f"CPU spike detected: {metrics['cpu_percent']:.1f}% (baseline: {avg_cpu:.1f}% ± {std_cpu:.1f}%)"
                })
        
        if len(self.packet_history) >= 10:
            avg_packets = sum(self.packet_history) / len(self.packet_history)
            std_packets = (sum((x - avg_packets) ** 2 for x in self.packet_history) / len(self.packet_history)) ** 0.5
            
            if metrics['packet_rate'] > avg_packets + 3 * std_packets:
                anomalies.append({
                    'type': 'packet_spike',
                    'severity': 'high',
                    'value': metrics['packet_rate'],
                    'baseline': avg_packets,
                    'message': f"Packet spike detected: {metrics['packet_rate']:.0f} pps (baseline: {avg_packets:.0f} ± {std_packets:.0f} pps)"
                })
        
        return anomalies
    
    def pattern_recognition(self, metrics):
        anomalies = []
        
        if len(self.cpu_history) >= 5:
            recent_cpu = list(self.cpu_history)[-5:]
            if all(recent_cpu[i] < recent_cpu[i+1] for i in range(len(recent_cpu)-1)):
                if recent_cpu[-1] > self.cpu_threshold * 0.8:
                    anomalies.append({
                        'type': 'escalating_cpu',
                        'severity': 'medium',
                        'pattern': 'increasing',
                        'message': f"Escalating CPU usage pattern detected"
                    })
        
        if len(self.packet_history) >= 5:
            recent_packets = list(self.packet_history)[-5:]
            if all(recent_packets[i] < recent_packets[i+1] for i in range(len(recent_packets)-1)):
                if recent_packets[-1] > self.packet_threshold * 0.7:
                    anomalies.append({
                        'type': 'escalating_traffic',
                        'severity': 'high',
                        'pattern': 'increasing',
                        'message': f"Escalating traffic pattern detected - possible attack ramp-up"
                    })
        
        return anomalies
    
    def detect_f1_anomalies(self):
        anomalies = []
        
        try:
            result = subprocess.run(
                ['ss', '-tunap', 'sport = :38472 or dport = :38472'],
                capture_output=True,
                text=True
            )
            f1c_connections = len(result.stdout.strip().split('\n')) - 1
            
            if f1c_connections > 100:
                anomalies.append({
                    'type': 'f1c_flood',
                    'severity': 'critical',
                    'value': f1c_connections,
                    'message': f"Excessive F1-C connections detected: {f1c_connections}"
                })
        except:
            pass
        
        try:
            result = subprocess.run(
                ['ss', '-tunap', 'sport = :2152 or dport = :2152'],
                capture_output=True,
                text=True
            )
            f1u_connections = len(result.stdout.strip().split('\n')) - 1
            
            if f1u_connections > 200:
                anomalies.append({
                    'type': 'f1u_flood',
                    'severity': 'critical',
                    'value': f1u_connections,
                    'message': f"Excessive F1-U connections detected: {f1u_connections}"
                })
        except:
            pass
        
        return anomalies
    
    def log_anomaly(self, anomaly):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            **anomaly
        }
        self.anomaly_log.append(log_entry)
        
        severity_colors = {
            'low': '\033[92m',
            'medium': '\033[93m',
            'high': '\033[91m',
            'critical': '\033[95m'
        }
        reset_color = '\033[0m'
        
        color = severity_colors.get(anomaly.get('severity', 'medium'), '\033[93m')
        logger.warning(f"{color}[{anomaly.get('severity', 'UNKNOWN').upper()}] {anomaly.get('message', 'Anomaly detected')}{reset_color}")
    
    def trigger_defense(self, anomalies):
        for anomaly in anomalies:
            if anomaly['severity'] in ['high', 'critical']:
                logger.info(f"Triggering defense mechanism for {anomaly['type']}")
                
                if anomaly['type'] == 'packet_flood':
                    self._apply_rate_limiting()
                elif anomaly['type'] == 'connection_flood':
                    self._apply_connection_limiting()
                elif anomaly['type'].startswith('f1'):
                    self._apply_f1_protection()
    
    def _apply_rate_limiting(self):
        logger.info("Applying rate limiting...")
        try:
            subprocess.run([
                'sudo', 'iptables', '-A', 'INPUT',
                '-p', 'udp', '--dport', '2152',
                '-m', 'limit', '--limit', '1000/sec',
                '-j', 'ACCEPT'
            ], check=False)
            subprocess.run([
                'sudo', 'iptables', '-A', 'INPUT',
                '-p', 'udp', '--dport', '2152',
                '-j', 'DROP'
            ], check=False)
            logger.info("Rate limiting applied successfully")
        except Exception as e:
            logger.error(f"Failed to apply rate limiting: {e}")
    
    def _apply_connection_limiting(self):
        logger.info("Applying connection limiting...")
        try:
            subprocess.run([
                'sudo', 'iptables', '-A', 'INPUT',
                '-p', 'tcp', '--syn',
                '-m', 'connlimit', '--connlimit-above', '100',
                '-j', 'REJECT'
            ], check=False)
            logger.info("Connection limiting applied successfully")
        except Exception as e:
            logger.error(f"Failed to apply connection limiting: {e}")
    
    def _apply_f1_protection(self):
        logger.info("Applying F1 interface protection...")
        try:
            subprocess.run([
                'sudo', 'iptables', '-A', 'INPUT',
                '-p', 'sctp', '--dport', '38472',
                '-m', 'limit', '--limit', '50/sec',
                '-j', 'ACCEPT'
            ], check=False)
            subprocess.run([
                'sudo', 'iptables', '-A', 'INPUT',
                '-p', 'sctp', '--dport', '38472',
                '-j', 'DROP'
            ], check=False)
            logger.info("F1 protection applied successfully")
        except Exception as e:
            logger.error(f"Failed to apply F1 protection: {e}")
    
    def export_anomaly_log(self, filename='anomaly_log.json'):
        try:
            with open(filename, 'w') as f:
                json.dump(self.anomaly_log, f, indent=2)
            logger.info(f"Anomaly log exported to {filename}")
        except Exception as e:
            logger.error(f"Failed to export anomaly log: {e}")
    
    def run(self, duration=None, auto_defense=False):
        logger.info("Starting attack detection...")
        logger.info(f"Auto-defense: {'Enabled' if auto_defense else 'Disabled'}")
        
        start_time = time.time()
        iteration = 0
        
        try:
            while self.detection_active:
                if duration and (time.time() - start_time >= duration):
                    logger.info(f"Detection duration ({duration}s) reached")
                    break
                
                metrics = self.collect_metrics()
                
                all_anomalies = []
                all_anomalies.extend(self.threshold_based_detection(metrics))
                all_anomalies.extend(self.statistical_analysis(metrics))
                all_anomalies.extend(self.pattern_recognition(metrics))
                all_anomalies.extend(self.detect_f1_anomalies())
                
                if all_anomalies:
                    for anomaly in all_anomalies:
                        self.log_anomaly(anomaly)
                    
                    if auto_defense:
                        self.trigger_defense(all_anomalies)
                
                iteration += 1
                if iteration % 10 == 0:
                    logger.info(f"[{iteration}] Monitoring... CPU: {metrics['cpu_percent']:.1f}%, "
                               f"Mem: {metrics['memory_percent']:.1f}%, "
                               f"Packets: {metrics['packet_rate']:.0f} pps, "
                               f"Connections: {metrics['connections']}")
                
                time.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("Detection stopped by user")
        finally:
            logger.info(f"Detection completed. Total anomalies detected: {len(self.anomaly_log)}")
            if self.anomaly_log:
                self.export_anomaly_log()
    
    def stop(self):
        self.detection_active = False

def main():
    parser = argparse.ArgumentParser(description='Attack Detection System')
    parser.add_argument('--cpu-threshold', type=int, default=80, help='CPU threshold (%)')
    parser.add_argument('--memory-threshold', type=int, default=85, help='Memory threshold (%)')
    parser.add_argument('--packet-threshold', type=int, default=10000, help='Packet rate threshold (pps)')
    parser.add_argument('--connection-threshold', type=int, default=1000, help='Connection count threshold')
    parser.add_argument('--duration', type=int, help='Detection duration in seconds')
    parser.add_argument('--auto-defense', action='store_true', help='Automatically trigger defense mechanisms')
    parser.add_argument('--export', default='anomaly_log.json', help='Export log filename')
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("Attack Detection System - SP5G Project")
    logger.info("="*60)
    
    detector = AttackDetector(
        cpu_threshold=args.cpu_threshold,
        memory_threshold=args.memory_threshold,
        packet_threshold=args.packet_threshold,
        connection_threshold=args.connection_threshold
    )
    
    try:
        detector.run(duration=args.duration, auto_defense=args.auto_defense)
    except Exception as e:
        logger.error(f"Detection error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()



