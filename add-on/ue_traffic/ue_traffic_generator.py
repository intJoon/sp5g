#!/usr/bin/env python3

import sys
import os
import time
import random
import logging
import argparse
import json
from datetime import datetime
from scapy.all import IP, UDP, Raw, send
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UETrafficProfile:
    def __init__(self, ue_type, ue_id, destination_ip, destination_port=2152):
        self.ue_type = ue_type
        self.ue_id = ue_id
        self.destination_ip = destination_ip
        self.destination_port = destination_port
        self.active = False
        self.stats = {
            'packets_sent': 0,
            'bytes_sent': 0,
            'start_time': None,
            'status': 'offline'
        }
        
    def get_profile(self):
        profiles = {
            'industrial_robot': {
                'name': 'Precision Industrial Robot Arm',
                'description': 'Handles hazardous materials with millisecond precision',
                'packet_size': 256,
                'interval': 0.001,
                'qos_requirement': 'URLLC',
                'latency_max_ms': 1,
                'reliability': 99.9999,
                'priority': 'critical',
                'data_pattern': 'periodic',
                'failure_impact': 'Material contamination, equipment damage, worker injury'
            },
            'autonomous_vehicle': {
                'name': 'Autonomous Vehicle',
                'description': 'Self-driving car requiring real-time navigation',
                'packet_size': 512,
                'interval': 0.01,
                'qos_requirement': 'URLLC',
                'latency_max_ms': 5,
                'reliability': 99.999,
                'priority': 'critical',
                'data_pattern': 'continuous',
                'failure_impact': 'Loss of control, collision, passenger injury'
            },
            'military_drone': {
                'name': 'Military Reconnaissance Drone',
                'description': 'Tactical drone for surveillance and targeting',
                'packet_size': 1024,
                'interval': 0.02,
                'qos_requirement': 'URLLC + eMBB',
                'latency_max_ms': 10,
                'reliability': 99.99,
                'priority': 'high',
                'data_pattern': 'burst',
                'failure_impact': 'Mission failure, drone crash, intelligence loss'
            },
            'smartphone': {
                'name': 'Consumer Smartphone',
                'description': 'Standard mobile device for voice/data',
                'packet_size': 512,
                'interval': 0.1,
                'qos_requirement': 'eMBB',
                'latency_max_ms': 50,
                'reliability': 99.9,
                'priority': 'normal',
                'data_pattern': 'random',
                'failure_impact': 'Service interruption, user inconvenience'
            },
            'broadcast_camera': {
                'name': 'Live Broadcast Camera',
                'description': '4K live video streaming',
                'packet_size': 1500,
                'interval': 0.005,
                'qos_requirement': 'eMBB',
                'latency_max_ms': 20,
                'reliability': 99.95,
                'priority': 'high',
                'data_pattern': 'continuous_high',
                'failure_impact': 'Broadcast disruption, viewer loss, revenue impact'
            }
        }
        return profiles.get(self.ue_type, profiles['smartphone'])
    
    def start_traffic(self, duration=None):
        self.active = True
        self.stats['status'] = 'online'
        self.stats['start_time'] = datetime.now().isoformat()
        
        profile = self.get_profile()
        logger.info(f"[{self.ue_type}:{self.ue_id}] Starting traffic generation")
        logger.info(f"  Profile: {profile['name']}")
        logger.info(f"  QoS: {profile['qos_requirement']}")
        logger.info(f"  Packet Size: {profile['packet_size']} bytes")
        logger.info(f"  Interval: {profile['interval']*1000:.1f}ms")
        
        start_time = time.time()
        
        try:
            while self.active:
                if duration and (time.time() - start_time) > duration:
                    break
                
                self._send_packet(profile)
                time.sleep(profile['interval'])
                
        except KeyboardInterrupt:
            logger.info(f"[{self.ue_type}:{self.ue_id}] Traffic stopped by user")
        except Exception as e:
            logger.error(f"[{self.ue_type}:{self.ue_id}] Error: {e}")
        finally:
            self.stop_traffic()
    
    def _send_packet(self, profile):
        try:
            payload_data = {
                'ue_type': self.ue_type,
                'ue_id': self.ue_id,
                'timestamp': time.time(),
                'seq': self.stats['packets_sent']
            }
            
            payload = json.dumps(payload_data).encode()
            payload += os.urandom(profile['packet_size'] - len(payload))
            
            packet = IP(dst=self.destination_ip) / UDP(dport=self.destination_port) / Raw(load=payload)
            send(packet, verbose=False)
            
            self.stats['packets_sent'] += 1
            self.stats['bytes_sent'] += len(payload)
            
            if self.stats['packets_sent'] % 1000 == 0:
                logger.info(f"[{self.ue_type}:{self.ue_id}] Sent {self.stats['packets_sent']} packets, "
                           f"{self.stats['bytes_sent']/1024/1024:.2f} MB")
                
        except Exception as e:
            logger.error(f"Failed to send packet: {e}")
    
    def stop_traffic(self):
        self.active = False
        self.stats['status'] = 'offline'
        
        elapsed = (time.time() - datetime.fromisoformat(self.stats['start_time']).timestamp()) if self.stats['start_time'] else 0
        
        logger.info(f"[{self.ue_type}:{self.ue_id}] Traffic stopped")
        logger.info(f"  Total packets: {self.stats['packets_sent']}")
        logger.info(f"  Total bytes: {self.stats['bytes_sent']/1024/1024:.2f} MB")
        logger.info(f"  Duration: {elapsed:.1f}s")
        if elapsed > 0:
            logger.info(f"  Average rate: {self.stats['packets_sent']/elapsed:.1f} pps")
    
    def get_stats(self):
        return self.stats.copy()

class UETrafficSimulator:
    def __init__(self, destination_ip):
        self.destination_ip = destination_ip
        self.ues = {}
        self.threads = {}
        
    def add_ue(self, ue_type, ue_id):
        ue = UETrafficProfile(ue_type, ue_id, self.destination_ip)
        self.ues[f"{ue_type}:{ue_id}"] = ue
        logger.info(f"Added UE: {ue_type}:{ue_id}")
        return ue
    
    def start_ue(self, ue_type, ue_id, duration=None):
        key = f"{ue_type}:{ue_id}"
        if key not in self.ues:
            logger.error(f"UE {key} not found")
            return
        
        ue = self.ues[key]
        thread = threading.Thread(target=ue.start_traffic, args=(duration,), daemon=True)
        self.threads[key] = thread
        thread.start()
        logger.info(f"Started UE traffic: {key}")
    
    def stop_ue(self, ue_type, ue_id):
        key = f"{ue_type}:{ue_id}"
        if key in self.ues:
            self.ues[key].stop_traffic()
    
    def start_all(self, duration=None):
        for key, ue in self.ues.items():
            self.start_ue(ue.ue_type, ue.ue_id, duration)
    
    def stop_all(self):
        for ue in self.ues.values():
            ue.stop_traffic()
        
        for thread in self.threads.values():
            thread.join(timeout=2)
    
    def get_all_stats(self):
        return {key: ue.get_stats() for key, ue in self.ues.items()}

def main():
    parser = argparse.ArgumentParser(description='5G UE Traffic Generator')
    parser.add_argument('--destination', '-d', required=True, help='Destination IP (e.g., DU IP)')
    parser.add_argument('--port', '-p', type=int, default=2152, help='Destination port (default: 2152)')
    parser.add_argument('--scenario', '-s', choices=['nuclear', 'highway', 'military', 'public', 'home', 'all'], 
                       default='all', help='Traffic scenario')
    parser.add_argument('--duration', '-t', type=int, default=60, help='Duration in seconds (0 for infinite)')
    parser.add_argument('--ue-types', nargs='+', 
                       choices=['industrial_robot', 'autonomous_vehicle', 'military_drone', 'smartphone', 'broadcast_camera'],
                       help='Specific UE types to simulate')
    
    args = parser.parse_args()
    
    simulator = UETrafficSimulator(args.destination)
    
    scenario_configs = {
        'nuclear': [
            ('industrial_robot', 'robot-1'),
            ('industrial_robot', 'robot-2'),
            ('smartphone', 'worker-1'),
            ('smartphone', 'worker-2')
        ],
        'highway': [
            ('autonomous_vehicle', 'car-1'),
            ('autonomous_vehicle', 'car-2'),
            ('autonomous_vehicle', 'car-3'),
            ('smartphone', 'passenger-1')
        ],
        'military': [
            ('military_drone', 'drone-1'),
            ('military_drone', 'drone-2'),
            ('broadcast_camera', 'recon-cam-1')
        ],
        'public': [
            ('broadcast_camera', 'news-cam-1'),
            ('smartphone', 'citizen-1'),
            ('smartphone', 'citizen-2'),
            ('smartphone', 'citizen-3')
        ],
        'home': [
            ('smartphone', 'phone-1'),
            ('smartphone', 'phone-2')
        ]
    }
    
    if args.ue_types:
        for i, ue_type in enumerate(args.ue_types):
            simulator.add_ue(ue_type, f"custom-{i+1}")
    elif args.scenario == 'all':
        all_ues = [
            ('industrial_robot', 'robot-1'),
            ('autonomous_vehicle', 'car-1'),
            ('military_drone', 'drone-1'),
            ('smartphone', 'phone-1'),
            ('broadcast_camera', 'camera-1')
        ]
        for ue_type, ue_id in all_ues:
            simulator.add_ue(ue_type, ue_id)
    else:
        for ue_type, ue_id in scenario_configs[args.scenario]:
            simulator.add_ue(ue_type, ue_id)
    
    duration = args.duration if args.duration > 0 else None
    
    logger.info("="*60)
    logger.info("Starting UE Traffic Simulation")
    logger.info(f"Scenario: {args.scenario}")
    logger.info(f"Destination: {args.destination}:{args.port}")
    logger.info(f"Duration: {duration if duration else 'Infinite (Ctrl+C to stop)'}")
    logger.info(f"Total UEs: {len(simulator.ues)}")
    logger.info("="*60)
    
    try:
        simulator.start_all(duration)
        
        if duration:
            time.sleep(duration + 2)
        else:
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        logger.info("\nStopping all UE traffic...")
    finally:
        simulator.stop_all()
        
        logger.info("\n" + "="*60)
        logger.info("Final Statistics:")
        logger.info("="*60)
        for key, stats in simulator.get_all_stats().items():
            logger.info(f"{key}: {stats['packets_sent']} packets, "
                       f"{stats['bytes_sent']/1024/1024:.2f} MB, "
                       f"status: {stats['status']}")

if __name__ == '__main__':
    main()

