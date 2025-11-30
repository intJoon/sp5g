#!/usr/bin/env python3

import argparse
import sys
import logging
import subprocess
from typing import List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IPFilter:
    def __init__(self):
        self.blocked_ips = []
        self.whitelist_ips = []
        
        logger.info("IP Filter initialized")
    
    def block_ip(self, ip_address: str, interface: str = None):
        try:
            cmd = ['sudo', 'iptables', '-A', 'INPUT', '-s', ip_address, '-j', 'DROP']
            if interface:
                cmd.insert(4, '-i')
                cmd.insert(5, interface)
            
            subprocess.run(cmd, check=True)
            self.blocked_ips.append(ip_address)
            logger.info(f"Blocked IP: {ip_address}")
            return True
        except Exception as e:
            logger.error(f"Failed to block IP {ip_address}: {e}")
            return False
    
    def block_ip_range(self, ip_range: str, interface: str = None):
        try:
            cmd = ['sudo', 'iptables', '-A', 'INPUT', '-s', ip_range, '-j', 'DROP']
            if interface:
                cmd.insert(4, '-i')
                cmd.insert(5, interface)
            
            subprocess.run(cmd, check=True)
            logger.info(f"Blocked IP range: {ip_range}")
            return True
        except Exception as e:
            logger.error(f"Failed to block IP range {ip_range}: {e}")
            return False
    
    def unblock_ip(self, ip_address: str):
        try:
            subprocess.run([
                'sudo', 'iptables', '-D', 'INPUT', '-s', ip_address, '-j', 'DROP'
            ], check=True)
            
            if ip_address in self.blocked_ips:
                self.blocked_ips.remove(ip_address)
            
            logger.info(f"Unblocked IP: {ip_address}")
            return True
        except Exception as e:
            logger.error(f"Failed to unblock IP {ip_address}: {e}")
            return False
    
    def whitelist_ip(self, ip_address: str):
        try:
            subprocess.run([
                'sudo', 'iptables', '-I', 'INPUT', '-s', ip_address, '-j', 'ACCEPT'
            ], check=True)
            
            self.whitelist_ips.append(ip_address)
            logger.info(f"Whitelisted IP: {ip_address}")
            return True
        except Exception as e:
            logger.error(f"Failed to whitelist IP {ip_address}: {e}")
            return False
    
    def block_port(self, port: int, protocol: str = 'tcp'):
        try:
            subprocess.run([
                'sudo', 'iptables', '-A', 'INPUT',
                '-p', protocol, '--dport', str(port),
                '-j', 'DROP'
            ], check=True)
            
            logger.info(f"Blocked {protocol.upper()} port: {port}")
            return True
        except Exception as e:
            logger.error(f"Failed to block port {port}: {e}")
            return False
    
    def allow_port(self, port: int, protocol: str = 'tcp'):
        try:
            subprocess.run([
                'sudo', 'iptables', '-I', 'INPUT',
                '-p', protocol, '--dport', str(port),
                '-j', 'ACCEPT'
            ], check=True)
            
            logger.info(f"Allowed {protocol.upper()} port: {port}")
            return True
        except Exception as e:
            logger.error(f"Failed to allow port {port}: {e}")
            return False
    
    def block_country(self, country_code: str):
        logger.info(f"Blocking traffic from country: {country_code}")
        logger.warning("Country blocking requires GeoIP database - not implemented in this version")
        return False
    
    def clear_all_rules(self):
        try:
            subprocess.run(['sudo', 'iptables', '-F'], check=True)
            subprocess.run(['sudo', 'iptables', '-X'], check=True)
            
            self.blocked_ips = []
            self.whitelist_ips = []
            
            logger.info("Cleared all firewall rules")
            return True
        except Exception as e:
            logger.error(f"Failed to clear rules: {e}")
            return False
    
    def list_rules(self):
        try:
            result = subprocess.run(
                ['sudo', 'iptables', '-L', '-n', '-v'],
                capture_output=True,
                text=True
            )
            
            logger.info("Current iptables rules:")
            print(result.stdout)
            return result.stdout
        except Exception as e:
            logger.error(f"Failed to list rules: {e}")
            return None
    
    def save_rules(self, filename='/etc/iptables/rules.v4'):
        try:
            result = subprocess.run(
                ['sudo', 'iptables-save'],
                capture_output=True,
                text=True
            )
            
            with open(filename, 'w') as f:
                f.write(result.stdout)
            
            logger.info(f"Saved iptables rules to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save rules: {e}")
            return False
    
    def restore_rules(self, filename='/etc/iptables/rules.v4'):
        try:
            with open(filename, 'r') as f:
                rules = f.read()
            
            subprocess.run(
                ['sudo', 'iptables-restore'],
                input=rules,
                text=True,
                check=True
            )
            
            logger.info(f"Restored iptables rules from {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore rules: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='IP Filtering and Firewall Management')
    parser.add_argument('--block-ip', nargs='+', help='Block specific IP addresses')
    parser.add_argument('--block-range', help='Block IP range (CIDR notation)')
    parser.add_argument('--unblock-ip', nargs='+', help='Unblock specific IP addresses')
    parser.add_argument('--whitelist-ip', nargs='+', help='Whitelist specific IP addresses')
    parser.add_argument('--block-port', type=int, help='Block specific port')
    parser.add_argument('--allow-port', type=int, help='Allow specific port')
    parser.add_argument('--protocol', default='tcp', choices=['tcp', 'udp', 'sctp'], help='Protocol for port filtering')
    parser.add_argument('--interface', help='Network interface to apply rules')
    parser.add_argument('--clear', action='store_true', help='Clear all firewall rules')
    parser.add_argument('--list', action='store_true', help='List current firewall rules')
    parser.add_argument('--save', help='Save rules to file')
    parser.add_argument('--restore', help='Restore rules from file')
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("IP Filtering System - SP5G Project")
    logger.info("="*60)
    
    filter_mgr = IPFilter()
    
    try:
        if args.clear:
            filter_mgr.clear_all_rules()
        
        if args.block_ip:
            for ip in args.block_ip:
                filter_mgr.block_ip(ip, args.interface)
        
        if args.block_range:
            filter_mgr.block_ip_range(args.block_range, args.interface)
        
        if args.unblock_ip:
            for ip in args.unblock_ip:
                filter_mgr.unblock_ip(ip)
        
        if args.whitelist_ip:
            for ip in args.whitelist_ip:
                filter_mgr.whitelist_ip(ip)
        
        if args.block_port:
            filter_mgr.block_port(args.block_port, args.protocol)
        
        if args.allow_port:
            filter_mgr.allow_port(args.allow_port, args.protocol)
        
        if args.list:
            filter_mgr.list_rules()
        
        if args.save:
            filter_mgr.save_rules(args.save)
        
        if args.restore:
            filter_mgr.restore_rules(args.restore)
        
        logger.info("Operation completed successfully")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()



