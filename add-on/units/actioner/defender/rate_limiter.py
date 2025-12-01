#!/usr/bin/env python3

import argparse
import sys
import logging
import subprocess
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        self.active_limits = []
        logger.info("Rate Limiter initialized")
    
    def limit_packets_per_second(self, port, rate, protocol='tcp', interface=None):
        try:
            cmd = [
                'sudo', 'iptables', '-A', 'INPUT',
                '-p', protocol, '--dport', str(port),
                '-m', 'limit', '--limit', f'{rate}/sec',
                '-j', 'ACCEPT'
            ]
            if interface:
                cmd.insert(4, '-i')
                cmd.insert(5, interface)
            
            subprocess.run(cmd, check=True)
            
            drop_cmd = [
                'sudo', 'iptables', '-A', 'INPUT',
                '-p', protocol, '--dport', str(port),
                '-j', 'DROP'
            ]
            if interface:
                drop_cmd.insert(4, '-i')
                drop_cmd.insert(5, interface)
            
            subprocess.run(drop_cmd, check=True)
            
            limit_info = {
                'port': port,
                'rate': rate,
                'protocol': protocol,
                'interface': interface
            }
            self.active_limits.append(limit_info)
            
            logger.info(f"Applied rate limit: {rate}/sec for {protocol.upper()} port {port}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply rate limit: {e}")
            return False
    
    def limit_connections(self, port, max_connections, protocol='tcp'):
        try:
            subprocess.run([
                'sudo', 'iptables', '-A', 'INPUT',
                '-p', protocol, '--dport', str(port), '--syn',
                '-m', 'connlimit', '--connlimit-above', str(max_connections),
                '-j', 'REJECT', '--reject-with', 'tcp-reset'
            ], check=True)
            
            logger.info(f"Limited connections to {max_connections} for {protocol.upper()} port {port}")
            return True
        except Exception as e:
            logger.error(f"Failed to limit connections: {e}")
            return False
    
    def limit_bandwidth(self, interface, rate_mbps):
        try:
            subprocess.run([
                'sudo', 'tc', 'qdisc', 'add', 'dev', interface,
                'root', 'tbf', 'rate', f'{rate_mbps}mbit',
                'burst', '32kbit', 'latency', '400ms'
            ], check=True)
            
            logger.info(f"Limited bandwidth on {interface} to {rate_mbps} Mbps")
            return True
        except Exception as e:
            logger.error(f"Failed to limit bandwidth: {e}")
            return False
    
    def remove_bandwidth_limit(self, interface):
        try:
            subprocess.run([
                'sudo', 'tc', 'qdisc', 'del', 'dev', interface, 'root'
            ], check=False)
            
            logger.info(f"Removed bandwidth limit on {interface}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove bandwidth limit: {e}")
            return False
    
    def dynamic_rate_adjust(self, port, protocol, monitor_duration=60, 
                           normal_threshold=1000, attack_threshold=5000):
        logger.info(f"Starting dynamic rate adjustment for {protocol.upper()} port {port}")
        logger.info(f"Monitor duration: {monitor_duration}s, "
                   f"Normal: {normal_threshold}/sec, Attack: {attack_threshold}/sec")
        
        import psutil
        
        start_time = time.time()
        current_limit = None
        
        try:
            while time.time() - start_time < monitor_duration:
                net_io_start = psutil.net_io_counters()
                time.sleep(1)
                net_io_end = psutil.net_io_counters()
                
                packets_per_sec = net_io_end.packets_recv - net_io_start.packets_recv
                
                if packets_per_sec > attack_threshold:
                    if current_limit != 'strict':
                        logger.warning(f"Attack detected ({packets_per_sec} pps) - Applying strict limit")
                        self.clear_port_rules(port, protocol)
                        self.limit_packets_per_second(port, 100, protocol)
                        current_limit = 'strict'
                
                elif packets_per_sec > normal_threshold:
                    if current_limit != 'moderate':
                        logger.info(f"High traffic detected ({packets_per_sec} pps) - Applying moderate limit")
                        self.clear_port_rules(port, protocol)
                        self.limit_packets_per_second(port, 1000, protocol)
                        current_limit = 'moderate'
                
                else:
                    if current_limit is not None:
                        logger.info(f"Normal traffic ({packets_per_sec} pps) - Removing limits")
                        self.clear_port_rules(port, protocol)
                        current_limit = None
                
                logger.info(f"Current traffic: {packets_per_sec} pps, Limit mode: {current_limit or 'none'}")
        
        except KeyboardInterrupt:
            logger.info("Dynamic rate adjustment stopped by user")
        finally:
            logger.info("Dynamic rate adjustment completed")
    
    def clear_port_rules(self, port, protocol):
        try:
            subprocess.run([
                'sudo', 'iptables', '-D', 'INPUT',
                '-p', protocol, '--dport', str(port),
                '-m', 'limit', '--limit', '100/sec',
                '-j', 'ACCEPT'
            ], check=False, capture_output=True)
            
            subprocess.run([
                'sudo', 'iptables', '-D', 'INPUT',
                '-p', protocol, '--dport', str(port),
                '-j', 'DROP'
            ], check=False, capture_output=True)
            
            return True
        except:
            return False
    
    def clear_all_limits(self):
        try:
            subprocess.run(['sudo', 'iptables', '-F'], check=True)
            subprocess.run(['sudo', 'iptables', '-X'], check=True)
            
            self.active_limits = []
            
            logger.info("Cleared all rate limits")
            return True
        except Exception as e:
            logger.error(f"Failed to clear limits: {e}")
            return False
    
    def list_limits(self):
        logger.info("Active rate limits:")
        for limit in self.active_limits:
            logger.info(f"  Port {limit['port']} ({limit['protocol']}): {limit['rate']}/sec")
        
        try:
            result = subprocess.run(
                ['sudo', 'iptables', '-L', '-n', '-v'],
                capture_output=True,
                text=True
            )
            print(result.stdout)
        except Exception as e:
            logger.error(f"Failed to list limits: {e}")

def main():
    parser = argparse.ArgumentParser(description='Rate Limiting System')
    parser.add_argument('--port', type=int, help='Port to apply rate limit')
    parser.add_argument('--protocol', default='tcp', choices=['tcp', 'udp', 'sctp'], 
                       help='Protocol to apply rate limit')
    parser.add_argument('--rate', type=int, help='Rate limit (packets per second)')
    parser.add_argument('--max-connections', type=int, help='Maximum concurrent connections')
    parser.add_argument('--interface', help='Network interface')
    parser.add_argument('--bandwidth', type=int, help='Bandwidth limit in Mbps')
    parser.add_argument('--dynamic', action='store_true', help='Enable dynamic rate adjustment')
    parser.add_argument('--duration', type=int, default=60, help='Duration for dynamic mode (seconds)')
    parser.add_argument('--clear', action='store_true', help='Clear all rate limits')
    parser.add_argument('--list', action='store_true', help='List active rate limits')
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("Rate Limiting System - SP5G Project")
    logger.info("="*60)
    
    limiter = RateLimiter()
    
    try:
        if args.clear:
            limiter.clear_all_limits()
        
        if args.port and args.rate:
            limiter.limit_packets_per_second(args.port, args.rate, args.protocol, args.interface)
        
        if args.port and args.max_connections:
            limiter.limit_connections(args.port, args.max_connections, args.protocol)
        
        if args.interface and args.bandwidth:
            limiter.limit_bandwidth(args.interface, args.bandwidth)
        
        if args.dynamic and args.port:
            limiter.dynamic_rate_adjust(args.port, args.protocol, args.duration)
        
        if args.list:
            limiter.list_limits()
        
        logger.info("Operation completed successfully")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()



