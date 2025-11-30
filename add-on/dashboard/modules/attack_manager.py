import os
import subprocess
import logging
import json
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class AttackManager:
    def __init__(self):
        self.attack_root = '/home/sp5g/sp5g/add-on/attack'
        self.current_attack = None
        self.attack_process = None
        self.attack_log = []
        
    def launch_attack(self, attack_type: str, target: str, params: Dict, mode: str = 'manual') -> Dict:
        try:
            if self.current_attack:
                return {
                    'status': 'error',
                    'message': 'An attack is already running. Please stop it first.'
                }
            
            logger.info(f"Launching {attack_type} attack on {target} with params: {params}")
            
            attack_config = {
                'type': attack_type,
                'target': target,
                'params': params,
                'mode': mode,
                'start_time': datetime.now().isoformat()
            }
            
            self.current_attack = attack_config
            
            command = self._build_attack_command(attack_type, target, params, mode)
            
            self.attack_log.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'launch',
                'config': attack_config,
                'command': command
            })
            
            return {
                'status': 'success',
                'message': f'{attack_type} attack launched successfully',
                'config': attack_config,
                'command': command
            }
        except Exception as e:
            logger.error(f"Error launching attack: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def stop_attack(self) -> Dict:
        try:
            if not self.current_attack:
                return {
                    'status': 'warning',
                    'message': 'No attack is currently running'
                }
            
            logger.info(f"Stopping attack: {self.current_attack['type']}")
            
            if self.attack_process:
                self.attack_process.terminate()
                self.attack_process.wait(timeout=5)
                self.attack_process = None
            
            subprocess.run(['sudo', 'pkill', '-f', 'sp5g_attack'], check=False)
            
            self.attack_log.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'stop',
                'attack': self.current_attack['type']
            })
            
            stopped_attack = self.current_attack
            self.current_attack = None
            
            return {
                'status': 'success',
                'message': 'Attack stopped successfully',
                'stopped_attack': stopped_attack
            }
        except Exception as e:
            logger.error(f"Error stopping attack: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_attack_status(self) -> Dict:
        return {
            'current_attack': self.current_attack,
            'is_running': self.current_attack is not None,
            'attack_log': self.attack_log[-10:]
        }
    
    def _build_attack_command(self, attack_type: str, target: str, params: Dict, mode: str) -> str:
        if 'f1c' in attack_type.lower():
            return self._build_f1c_attack_command(attack_type, target, params, mode)
        elif 'f1u' in attack_type.lower():
            return self._build_f1u_attack_command(attack_type, target, params, mode)
        elif attack_type == 'distributed_ddos':
            return self._build_distributed_attack_command(target, params, mode)
        else:
            return self._build_generic_attack_command(attack_type, target, params, mode)
    
    def _build_f1c_attack_command(self, attack_type: str, target: str, params: Dict, mode: str) -> str:
        script_path = os.path.join(self.attack_root, 'f1c', 'f1c_attack.py')
        
        cmd_parts = [
            'sudo',
            'python3',
            script_path,
            '--type', attack_type,
            '--target', target,
            '--mode', mode
        ]
        
        if params.get('rate'):
            cmd_parts.extend(['--rate', str(params['rate'])])
        if params.get('duration'):
            cmd_parts.extend(['--duration', str(params['duration'])])
        if params.get('ue_count'):
            cmd_parts.extend(['--ue-count', str(params['ue_count'])])
        
        return ' '.join(cmd_parts)
    
    def _build_f1u_attack_command(self, attack_type: str, target: str, params: Dict, mode: str) -> str:
        script_path = os.path.join(self.attack_root, 'f1u', 'f1u_attack.py')
        
        cmd_parts = [
            'sudo',
            'python3',
            script_path,
            '--type', attack_type,
            '--target', target,
            '--mode', mode
        ]
        
        if params.get('packet_size'):
            cmd_parts.extend(['--packet-size', str(params['packet_size'])])
        if params.get('rate'):
            cmd_parts.extend(['--rate', str(params['rate'])])
        if params.get('duration'):
            cmd_parts.extend(['--duration', str(params['duration'])])
        
        return ' '.join(cmd_parts)
    
    def _build_distributed_attack_command(self, target: str, params: Dict, mode: str) -> str:
        script_path = os.path.join(self.attack_root, 'botnet', 'botnet_controller.py')
        
        cmd_parts = [
            'sudo',
            'python3',
            script_path,
            '--target', target,
            '--mode', mode
        ]
        
        if params.get('bot_count'):
            cmd_parts.extend(['--bots', str(params['bot_count'])])
        if params.get('rate'):
            cmd_parts.extend(['--rate', str(params['rate'])])
        
        return ' '.join(cmd_parts)
    
    def _build_generic_attack_command(self, attack_type: str, target: str, params: Dict, mode: str) -> str:
        return f"sudo python3 {self.attack_root}/generic_attack.py --type {attack_type} --target {target}"
    
    def get_attack_templates(self) -> Dict:
        return {
            'massive_ue_connection': {
                'name': 'Massive UE Connection Flooding',
                'category': 'f1c',
                'description': 'Flood CU with massive UE connection requests',
                'default_params': {
                    'ue_count': 1000,
                    'rate': 100,
                    'duration': 60
                }
            },
            'bearer_flooding': {
                'name': 'Bearer Flooding Attack',
                'category': 'f1c',
                'description': 'Exhaust bearer resources',
                'default_params': {
                    'bearer_count': 500,
                    'rate': 50,
                    'duration': 60
                }
            },
            'udp_flood': {
                'name': 'UDP Flood Attack',
                'category': 'f1u',
                'description': 'Flood F1-U interface with UDP packets',
                'default_params': {
                    'packet_size': 1024,
                    'rate': 10000,
                    'duration': 60
                }
            },
            'distributed_ddos': {
                'name': 'Distributed DDoS',
                'category': 'advanced',
                'description': 'Coordinated attack from multiple botnets',
                'default_params': {
                    'bot_count': 10,
                    'rate': 5000,
                    'duration': 60
                }
            }
        }



