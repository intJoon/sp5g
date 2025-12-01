#!/usr/bin/env python3

import argparse
import sys
import time
import logging
import json
import os
from datetime import datetime
from scapy.all import *
from scapy.layers.l2 import ARP, Ether
from scapy.layers.inet import IP, TCP, UDP
from scapy.contrib.sctp import SCTP
import threading
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NetworkSniffer:
    def __init__(self, interface=None, output_file='sniffed_data.json'):
        self.interface = interface or conf.iface
        self.output_file = output_file
        self.discovered_hosts = {}
        self.discovered_services = defaultdict(set)
        self.captured_packets = []
        self.sniffing = False
        self.stats = {
            'total_packets': 0,
            'arp_packets': 0,
            'ip_packets': 0,
            'tcp_packets': 0,
            'udp_packets': 0,
            'sctp_packets': 0,
            'start_time': None
        }
        
        logger.info(f"Network Sniffer initialized on interface: {self.interface}")
    
    def arp_scan(self, target_network="192.168.1.0/24", timeout=3):
        logger.info(f"Starting ARP scan on {target_network}")
        
        answered, unanswered = arping(target_network, timeout=timeout, verbose=False)
        
        for sent, received in answered:
            ip = received.psrc
            mac = received.hwsrc
            
            self.discovered_hosts[ip] = {
                'mac': mac,
                'first_seen': datetime.now().isoformat(),
                'vendor': self._get_vendor(mac),
                'ports': []
            }
            
            logger.info(f"Discovered: {ip} ({mac})")
        
        logger.info(f"ARP scan complete. Found {len(self.discovered_hosts)} hosts")
        return self.discovered_hosts
    
    def _get_vendor(self, mac):
        oui_map = {
            '00:0c:29': 'VMware',
            '00:50:56': 'VMware',
            '08:00:27': 'VirtualBox',
            '52:54:00': 'QEMU/KVM',
            '00:16:3e': 'Xen',
            '02:42:ac': 'Docker'
        }
        
        prefix = mac[:8].lower()
        return oui_map.get(prefix, 'Unknown')
    
    def passive_sniff(self, count=100, timeout=60, filter_str=None):
        logger.info(f"Starting passive sniffing (count={count}, timeout={timeout}s)")
        
        self.sniffing = True
        self.stats['start_time'] = datetime.now().isoformat()
        
        try:
            packets = sniff(
                iface=self.interface,
                count=count,
                timeout=timeout,
                filter=filter_str,
                prn=self._packet_callback,
                store=True
            )
            
            self.captured_packets.extend(packets)
            
        except KeyboardInterrupt:
            logger.info("Sniffing interrupted by user")
        except Exception as e:
            logger.error(f"Sniffing error: {e}")
        finally:
            self.sniffing = False
        
        logger.info(f"Passive sniffing complete. Captured {len(self.captured_packets)} packets")
        return self.captured_packets
    
    def _packet_callback(self, packet):
        self.stats['total_packets'] += 1
        
        if ARP in packet:
            self.stats['arp_packets'] += 1
            self._process_arp(packet)
        
        if IP in packet:
            self.stats['ip_packets'] += 1
            self._process_ip(packet)
        
        if TCP in packet:
            self.stats['tcp_packets'] += 1
            self._process_tcp(packet)
        
        if UDP in packet:
            self.stats['udp_packets'] += 1
            self._process_udp(packet)
        
        if SCTP in packet:
            self.stats['sctp_packets'] += 1
            self._process_sctp(packet)
        
        if self.stats['total_packets'] % 100 == 0:
            logger.info(f"Processed {self.stats['total_packets']} packets")
    
    def _process_arp(self, packet):
        if packet[ARP].op == 2:
            ip = packet[ARP].psrc
            mac = packet[ARP].hwsrc
            
            if ip not in self.discovered_hosts:
                self.discovered_hosts[ip] = {
                    'mac': mac,
                    'first_seen': datetime.now().isoformat(),
                    'vendor': self._get_vendor(mac),
                    'ports': []
                }
    
    def _process_ip(self, packet):
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        
        if src_ip not in self.discovered_hosts:
            self.discovered_hosts[src_ip] = {
                'mac': 'Unknown',
                'first_seen': datetime.now().isoformat(),
                'vendor': 'Unknown',
                'ports': []
            }
    
    def _process_tcp(self, packet):
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        sport = packet[TCP].sport
        dport = packet[TCP].dport
        
        self.discovered_services[dst_ip].add(('tcp', dport))
        
        if dport not in self.discovered_hosts.get(dst_ip, {}).get('ports', []):
            if dst_ip in self.discovered_hosts:
                self.discovered_hosts[dst_ip]['ports'].append(dport)
    
    def _process_udp(self, packet):
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        sport = packet[UDP].sport
        dport = packet[UDP].dport
        
        self.discovered_services[dst_ip].add(('udp', dport))
        
        if dport == 2152:
            logger.debug(f"F1-U traffic detected: {src_ip}:{sport} -> {dst_ip}:{dport}")
    
    def _process_sctp(self, packet):
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        sport = packet[SCTP].sport
        dport = packet[SCTP].dport
        
        self.discovered_services[dst_ip].add(('sctp', dport))
        
        if dport == 38472:
            logger.debug(f"F1-C traffic detected: {src_ip}:{sport} -> {dst_ip}:{dport}")
    
    def identify_5g_components(self):
        components = {
            'cu_cp': [],
            'cu_up': [],
            'du': [],
            'core': []
        }
        
        for ip, services in self.discovered_services.items():
            service_list = list(services)
            
            for proto, port in service_list:
                if proto == 'sctp' and port == 38472:
                    components['cu_cp'].append(ip)
                    logger.info(f"Identified CU-CP: {ip} (SCTP port 38472)")
                
                if proto == 'udp' and port == 2152:
                    components['cu_up'].append(ip)
                    logger.info(f"Identified CU-UP or DU: {ip} (GTP-U port 2152)")
                
                if proto == 'udp' and port == 2123:
                    components['core'].append(ip)
                    logger.info(f"Identified 5G Core component: {ip} (GTP-C port 2123)")
        
        return components
    
    def extract_credentials(self, keywords=['password', 'user', 'login', 'auth', 'token']):
        logger.info("Searching for potential credentials in captured packets...")
        
        credentials = []
        
        for packet in self.captured_packets:
            if packet.haslayer(Raw):
                payload = packet[Raw].load.decode('utf-8', errors='ignore').lower()
                
                for keyword in keywords:
                    if keyword in payload:
                        credentials.append({
                            'timestamp': datetime.now().isoformat(),
                            'src': packet[IP].src if packet.haslayer(IP) else 'N/A',
                            'dst': packet[IP].dst if packet.haslayer(IP) else 'N/A',
                            'keyword': keyword,
                            'snippet': payload[:200]
                        })
                        
                        logger.warning(f"Potential credential found: {keyword} in packet from {packet[IP].src}")
        
        logger.info(f"Found {len(credentials)} potential credential leaks")
        return credentials
    
    def save_results(self):
        results = {
            'scan_time': datetime.now().isoformat(),
            'interface': self.interface,
            'statistics': self.stats,
            'discovered_hosts': self.discovered_hosts,
            'discovered_services': {
                ip: [{'protocol': proto, 'port': port} for proto, port in services]
                for ip, services in self.discovered_services.items()
            },
            '5g_components': self.identify_5g_components()
        }
        
        with open(self.output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {self.output_file}")
        
        with open('discovered_targets.txt', 'w') as f:
            f.write("="*80 + "\n")
            f.write("DISCOVERED 5G NETWORK TARGETS\n")
            f.write("="*80 + "\n\n")
            
            components = self.identify_5g_components()
            
            f.write("CU-CP (Control Plane):\n")
            for ip in components['cu_cp']:
                f.write(f"  - {ip}:38472 (SCTP)\n")
            
            f.write("\nCU-UP / DU (User Plane):\n")
            for ip in components['cu_up']:
                f.write(f"  - {ip}:2152 (GTP-U)\n")
            
            f.write("\n5G Core Components:\n")
            for ip in components['core']:
                f.write(f"  - {ip}:2123 (GTP-C)\n")
            
            f.write("\nAll Discovered Hosts:\n")
            for ip, info in self.discovered_hosts.items():
                f.write(f"  {ip} ({info['mac']}) - {info['vendor']}\n")
                if info['ports']:
                    f.write(f"    Open ports: {', '.join(map(str, info['ports']))}\n")
        
        logger.info("Target list saved to discovered_targets.txt")
        
        return results
    
    def print_summary(self):
        print("\n" + "="*80)
        print("NETWORK SNIFFING SUMMARY")
        print("="*80)
        
        print(f"\nTotal Packets Captured: {self.stats['total_packets']}")
        print(f"  ARP: {self.stats['arp_packets']}")
        print(f"  IP: {self.stats['ip_packets']}")
        print(f"  TCP: {self.stats['tcp_packets']}")
        print(f"  UDP: {self.stats['udp_packets']}")
        print(f"  SCTP: {self.stats['sctp_packets']}")
        
        print(f"\nDiscovered Hosts: {len(self.discovered_hosts)}")
        for ip, info in sorted(self.discovered_hosts.items()):
            print(f"  {ip:15} {info['mac']:17} {info['vendor']}")
        
        components = self.identify_5g_components()
        
        print(f"\n5G Network Components:")
        print(f"  CU-CP: {len(components['cu_cp'])} ({', '.join(components['cu_cp'])})")
        print(f"  CU-UP/DU: {len(components['cu_up'])} ({', '.join(components['cu_up'])})")
        print(f"  Core: {len(components['core'])} ({', '.join(components['core'])})")
        
        print("\n" + "="*80)

def main():
    parser = argparse.ArgumentParser(description='5G Network Sniffer and Reconnaissance Tool')
    parser.add_argument('--interface', '-i', help='Network interface to sniff on')
    parser.add_argument('--arp-scan', '-a', help='Perform ARP scan on network (e.g., 192.168.1.0/24)')
    parser.add_argument('--passive', '-p', action='store_true', help='Passive sniffing mode')
    parser.add_argument('--count', '-c', type=int, default=1000, help='Number of packets to capture')
    parser.add_argument('--timeout', '-t', type=int, default=60, help='Sniffing timeout in seconds')
    parser.add_argument('--filter', '-f', help='BPF filter string (e.g., "port 38472")')
    parser.add_argument('--output', '-o', default='sniffed_data.json', help='Output JSON file')
    
    args = parser.parse_args()
    
    if os.geteuid() != 0:
        logger.error("This script requires root privileges. Please run with sudo.")
        sys.exit(1)
    
    sniffer = NetworkSniffer(interface=args.interface, output_file=args.output)
    
    logger.info("="*80)
    logger.info("5G Network Sniffer - Attack Reconnaissance")
    logger.info("="*80)
    
    if args.arp_scan:
        sniffer.arp_scan(target_network=args.arp_scan)
    
    if args.passive or not args.arp_scan:
        sniffer.passive_sniff(count=args.count, timeout=args.timeout, filter_str=args.filter)
    
    sniffer.save_results()
    sniffer.print_summary()
    
    logger.info("\n✓ Sniffing complete. Use discovered_targets.txt for attack planning.")

if __name__ == '__main__':
    main()

