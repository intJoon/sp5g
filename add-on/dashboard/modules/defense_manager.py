import os
import subprocess
import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

class DefenseManager:
    def __init__(self):
        self.defense_root = '/home/sp5g/sp5g/add-on/defense'
        self.active_defenses = []
        self.defense_log = []
        
    def enable_defense(self, defense_type: str, params: Dict) -> Dict:
        try:
            logger.info(f"Enabling defense: {defense_type} with params: {params}")
            
            defense_config = {
                'type': defense_type,
                'params': params,
                'start_time': datetime.now().isoformat()
            }
            
            command = self._build_defense_command(defense_type, params)
            
            self.active_defenses.append(defense_config)
            
            self.defense_log.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'enable',
                'config': defense_config,
                'command': command
            })
            
            return {
                'status': 'success',
                'message': f'{defense_type} defense enabled successfully',
                'config': defense_config,
                'command': command
            }
        except Exception as e:
            logger.error(f"Error enabling defense: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def disable_defense(self) -> Dict:
        try:
            logger.info("Disabling all defenses...")
            
            subprocess.run(['sudo', 'pkill', '-f', 'sp5g_defense'], check=False)
            
            self._clear_iptables_rules()
            
            self.defense_log.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'disable_all',
                'defenses': self.active_defenses
            })
            
            disabled_defenses = self.active_defenses
            self.active_defenses = []
            
            return {
                'status': 'success',
                'message': 'All defenses disabled successfully',
                'disabled_defenses': disabled_defenses
            }
        except Exception as e:
            logger.error(f"Error disabling defenses: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_defense_status(self) -> Dict:
        return {
            'active_defenses': self.active_defenses,
            'is_active': len(self.active_defenses) > 0,
            'defense_log': self.defense_log[-10:]
        }
    
    def _build_defense_command(self, defense_type: str, params: Dict) -> str:
        if defense_type == 'ip_filtering':
            return self._build_ip_filter_command(params)
        elif defense_type == 'rate_limiting':
            return self._build_rate_limit_command(params)
        elif defense_type == 'dynamic_throttling':
            return self._build_dynamic_throttle_command(params)
        elif defense_type == 'threshold_based':
            return self._build_threshold_detection_command(params)
        else:
            return self._build_generic_defense_command(defense_type, params)
    
    def _build_ip_filter_command(self, params: Dict) -> str:
        blocked_ips = params.get('blocked_ips', [])
        interface = params.get('interface', 'eth0')
        
        commands = []
        for ip in blocked_ips:
            cmd = f"sudo iptables -A INPUT -s {ip} -i {interface} -j DROP"
            commands.append(cmd)
        
        return ' && '.join(commands) if commands else 'echo "No IPs to block"'
    
    def _build_rate_limit_command(self, params: Dict) -> str:
        rate = params.get('rate', 100)
        interface = params.get('interface', 'eth0')
        port = params.get('port', 38472)
        
        cmd = (
            f"sudo iptables -A INPUT -p tcp --dport {port} -i {interface} "
            f"-m limit --limit {rate}/sec -j ACCEPT && "
            f"sudo iptables -A INPUT -p tcp --dport {port} -i {interface} -j DROP"
        )
        
        return cmd
    
    def _build_dynamic_throttle_command(self, params: Dict) -> str:
        script_path = os.path.join(self.defense_root, 'dynamic_throttle.py')
        
        cmd_parts = [
            'sudo',
            'python3',
            script_path,
            '--threshold', str(params.get('threshold', 1000)),
            '--action', params.get('action', 'limit')
        ]
        
        return ' '.join(cmd_parts)
    
    def _build_threshold_detection_command(self, params: Dict) -> str:
        script_path = os.path.join(self.defense_root, 'detector.py')
        
        cmd_parts = [
            'sudo',
            'python3',
            script_path,
            '--cpu-threshold', str(params.get('cpu_threshold', 80)),
            '--memory-threshold', str(params.get('memory_threshold', 85)),
            '--packet-threshold', str(params.get('packet_threshold', 10000))
        ]
        
        return ' '.join(cmd_parts)
    
    def _build_generic_defense_command(self, defense_type: str, params: Dict) -> str:
        return f"sudo python3 {self.defense_root}/generic_defense.py --type {defense_type}"
    
    def _clear_iptables_rules(self):
        try:
            subprocess.run(['sudo', 'iptables', '-F'], check=False)
            subprocess.run(['sudo', 'iptables', '-X'], check=False)
            logger.info("Cleared iptables rules")
        except Exception as e:
            logger.error(f"Error clearing iptables rules: {e}")
    
    def get_defense_templates(self) -> Dict:
        return {
            'ip_filtering': {
                'name': 'IP-based Filtering',
                'category': 'mitigation',
                'description': 'Block traffic from specific IP addresses',
                'default_params': {
                    'blocked_ips': [],
                    'interface': 'eth0'
                }
            },
            'rate_limiting': {
                'name': 'Rate Limiting',
                'category': 'mitigation',
                'description': 'Limit packet rate per second',
                'default_params': {
                    'rate': 100,
                    'port': 38472,
                    'interface': 'eth0'
                }
            },
            'dynamic_throttling': {
                'name': 'Dynamic Throttling',
                'category': 'mitigation',
                'description': 'Automatically adjust rate limits based on load',
                'default_params': {
                    'threshold': 1000,
                    'action': 'limit'
                }
            },
            'threshold_based': {
                'name': 'Threshold-based Detection',
                'category': 'detection',
                'description': 'Detect anomalies based on thresholds',
                'default_params': {
                    'cpu_threshold': 80,
                    'memory_threshold': 85,
                    'packet_threshold': 10000
                }
            }
        }



