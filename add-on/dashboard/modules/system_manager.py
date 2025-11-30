import os
import subprocess
import logging
import time
import re
import threading
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SystemManager:
    def __init__(self):
        self.oai_root = '/home/sp5g/sp5g'
        self.addon_path = '/home/sp5g/sp5g/add-on'
        self.cn5g_path = os.path.join(self.addon_path, 'ci-scripts/yaml_files/5g_rfsimulator_custom_v2.1.10')
        self.cn5g_fallback = os.path.expanduser('~/oai-cn5g')
        self.namespaces = {}
        self.max_attempts = 8
        self.wait_time = 5
        
        if not os.path.exists(self.cn5g_path):
            logger.warning(f"Primary docker-compose path not found: {self.cn5g_path}")
            if os.path.exists(self.cn5g_fallback):
                self.cn5g_path = self.cn5g_fallback
                logger.info(f"Using fallback path: {self.cn5g_fallback}")
            else:
                logger.warning("No docker-compose path found, Docker operations will fail")
        
    def get_system_status(self) -> Dict:
        try:
            status = {
                'cn5g': self._check_cn5g_status(),
                'gnb': self._check_gnb_status(),
                'ue': self._check_ue_status(),
                'namespaces': self._check_namespaces_status()
            }
            return status
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
    
    def get_network_status(self) -> Dict:
        try:
            return {
                'interfaces': self._get_network_interfaces(),
                'namespaces': self._list_namespaces(),
                'connections': self._get_active_connections()
            }
        except Exception as e:
            logger.error(f"Error getting network status: {e}")
            return {'error': str(e)}
    
    def start_system(self) -> Dict:
        try:
            logger.info("Starting 5G system...")
            
            result = self._run_command("docker compose up -d mysql oai-amf oai-smf oai-upf")
            if not result['success']:
                return {'status': 'error', 'message': 'Core Network start failed'}
            
            if not self.wait_for_core_network_ready():
                return {'status': 'error', 'message': 'Core Network not ready'}
            
            gnb_result = self._run_command("docker compose up -d oai-cucp oai-cuup oai-cuup2 oai-du oai-du2 oai-du3")
            if not gnb_result['success']:
                return {'status': 'error', 'message': 'gNB components start failed'}
            
            if not self.wait_for_gnb_ready():
                return {'status': 'error', 'message': 'gNB components not ready'}
            
            if not self.start_ue_sequence():
                return {'status': 'error', 'message': 'UE instances start failed'}
            
            return {'status': 'success', 'message': '5G system started successfully'}
        except Exception as e:
            logger.error(f"Error starting system: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def stop_system(self) -> Dict:
        try:
            logger.info("Stopping 5G system...")
            
            self._stop_gnb()
            
            self._stop_cn5g()
            
            return {'status': 'success', 'message': '5G system stopped successfully'}
        except Exception as e:
            logger.error(f"Error stopping system: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def restart_system(self) -> Dict:
        try:
            logger.info("Restarting 5G system...")
            
            stop_result = self._run_command("docker compose down")
            time.sleep(self.wait_time)
            
            start_result = self._run_command("docker compose up -d mysql oai-amf oai-smf oai-upf")
            if not start_result['success']:
                return {'status': 'error', 'message': 'Restart failed'}
            
            if not self.wait_for_core_network_ready():
                return {'status': 'error', 'message': 'Core Network not ready'}
            
            gnb_result = self._run_command("docker compose up -d oai-cucp oai-cuup oai-cuup2 oai-du oai-du2 oai-du3")
            if not gnb_result['success']:
                return {'status': 'error', 'message': 'gNB components restart failed'}
            
            if not self.wait_for_gnb_ready():
                return {'status': 'error', 'message': 'gNB components not ready'}
            
            if not self.start_ue_sequence():
                return {'status': 'error', 'message': 'UE instances restart failed'}
            
            return {'status': 'success', 'message': '5G system restarted successfully'}
        except Exception as e:
            logger.error(f"Error restarting system: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def setup_network_namespaces(self) -> Dict:
        try:
            logger.info("Setting up network namespaces...")
            
            namespaces = {
                'core': 'sp5g-core',
                'attacker': 'sp5g-attacker',
                'botnet': 'sp5g-botnet',
                'detector': 'sp5g-detector',
                'defender': 'sp5g-defender'
            }
            
            for name, ns in namespaces.items():
                self._create_namespace(ns)
            
            self._setup_namespace_networking(namespaces)
            
            self.namespaces = namespaces
            
            return {
                'status': 'success',
                'message': 'Network namespaces created successfully',
                'namespaces': namespaces
            }
        except Exception as e:
            logger.error(f"Error setting up namespaces: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def cleanup_network_namespaces(self) -> Dict:
        try:
            logger.info("Cleaning up network namespaces...")
            
            result = subprocess.run(
                ['sudo', 'ip', 'netns', 'list'],
                capture_output=True,
                text=True
            )
            
            for line in result.stdout.strip().split('\n'):
                if 'sp5g-' in line:
                    ns_name = line.split()[0]
                    subprocess.run(['sudo', 'ip', 'netns', 'del', ns_name], check=False)
            
            self.namespaces = {}
            
            return {'status': 'success', 'message': 'Network namespaces cleaned up'}
        except Exception as e:
            logger.error(f"Error cleaning up namespaces: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _check_cn5g_status(self) -> str:
        try:
            if not os.path.exists(self.cn5g_path):
                return 'not_installed'
            
            result = subprocess.run(
                ['docker', 'ps', '--filter', 'name=oai', '--format', '{{.Names}}'],
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip():
                return 'running'
            return 'stopped'
        except Exception as e:
            logger.error(f"Error checking CN5G status: {e}")
            return 'unknown'
    
    def _check_gnb_status(self) -> str:
        try:
            result = subprocess.run(
                ['pgrep', '-f', 'nr-softmodem'],
                capture_output=True
            )
            return 'running' if result.returncode == 0 else 'stopped'
        except Exception as e:
            logger.error(f"Error checking gNB status: {e}")
            return 'unknown'
    
    def _check_ue_status(self) -> str:
        try:
            result = subprocess.run(
                ['pgrep', '-f', 'nr-uesoftmodem'],
                capture_output=True
            )
            return 'running' if result.returncode == 0 else 'stopped'
        except Exception as e:
            logger.error(f"Error checking UE status: {e}")
            return 'unknown'
    
    def _check_namespaces_status(self) -> List[str]:
        try:
            result = subprocess.run(
                ['sudo', 'ip', 'netns', 'list'],
                capture_output=True,
                text=True
            )
            
            namespaces = []
            for line in result.stdout.strip().split('\n'):
                if line and 'sp5g-' in line:
                    namespaces.append(line.split()[0])
            
            return namespaces
        except Exception as e:
            logger.error(f"Error checking namespaces: {e}")
            return []
    
    def _get_network_interfaces(self) -> List[Dict]:
        try:
            result = subprocess.run(
                ['ip', '-j', 'addr'],
                capture_output=True,
                text=True
            )
            
            import json
            return json.loads(result.stdout)
        except Exception as e:
            logger.error(f"Error getting network interfaces: {e}")
            return []
    
    def _list_namespaces(self) -> List[str]:
        return self._check_namespaces_status()
    
    def _get_active_connections(self) -> List[Dict]:
        try:
            result = subprocess.run(
                ['ss', '-tunap'],
                capture_output=True,
                text=True
            )
            
            connections = []
            for line in result.stdout.strip().split('\n')[1:]:
                if line:
                    parts = line.split()
                    if len(parts) >= 5:
                        connections.append({
                            'protocol': parts[0],
                            'state': parts[1] if len(parts) > 1 else 'N/A',
                            'local': parts[4] if len(parts) > 4 else 'N/A'
                        })
            
            return connections[:50]
        except Exception as e:
            logger.error(f"Error getting active connections: {e}")
            return []
    
    def _start_cn5g(self):
        if os.path.exists(self.cn5g_path):
            logger.info("Starting CN5G containers...")
            subprocess.run(
                ['docker', 'compose', 'up', '-d'],
                cwd=self.cn5g_path,
                check=False
            )
    
    def _stop_cn5g(self):
        if os.path.exists(self.cn5g_path):
            logger.info("Stopping CN5G containers...")
            subprocess.run(
                ['docker', 'compose', 'down'],
                cwd=self.cn5g_path,
                check=False
            )
    
    def _start_gnb(self):
        logger.info("gNB start command prepared (manual start required)")
        pass
    
    def _stop_gnb(self):
        logger.info("Stopping gNB...")
        subprocess.run(['sudo', 'pkill', '-f', 'nr-softmodem'], check=False)
    
    def _create_namespace(self, ns_name: str):
        try:
            subprocess.run(['sudo', 'ip', 'netns', 'add', ns_name], check=False)
            subprocess.run(['sudo', 'ip', 'netns', 'exec', ns_name, 'ip', 'link', 'set', 'lo', 'up'], check=False)
            logger.info(f"Created namespace: {ns_name}")
        except Exception as e:
            logger.error(f"Error creating namespace {ns_name}: {e}")
    
    def _setup_namespace_networking(self, namespaces: Dict):
        try:
            base_subnet = 10
            
            for idx, (name, ns) in enumerate(namespaces.items(), start=1):
                veth_host = f"veth-{name}-h"
                veth_ns = f"veth-{name}-n"
                
                subprocess.run(['sudo', 'ip', 'link', 'add', veth_host, 'type', 'veth', 'peer', 'name', veth_ns], check=False)
                
                subprocess.run(['sudo', 'ip', 'link', 'set', veth_ns, 'netns', ns], check=False)
                
                host_ip = f"10.{base_subnet}.{idx}.1/24"
                ns_ip = f"10.{base_subnet}.{idx}.2/24"
                
                subprocess.run(['sudo', 'ip', 'addr', 'add', host_ip, 'dev', veth_host], check=False)
                subprocess.run(['sudo', 'ip', 'link', 'set', veth_host, 'up'], check=False)
                
                subprocess.run(['sudo', 'ip', 'netns', 'exec', ns, 'ip', 'addr', 'add', ns_ip, 'dev', veth_ns], check=False)
                subprocess.run(['sudo', 'ip', 'netns', 'exec', ns, 'ip', 'link', 'set', veth_ns, 'up'], check=False)
                
                logger.info(f"Configured network for namespace {ns}: {ns_ip}")
        except Exception as e:
            logger.error(f"Error setting up namespace networking: {e}")
    
    def _run_command(self, cmd: str, timeout: int = 30) -> Dict:
        try:
            if self.cn5g_path and os.path.exists(self.cn5g_path):
                result = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=self.cn5g_path,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            else:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'stderr': 'Command timeout', 'returncode': -1}
        except Exception as e:
            return {'success': False, 'stderr': str(e), 'returncode': -1}
    
    def wait_for_core_network_ready(self) -> bool:
        containers = [
            ("rfsim5g-mysql", "MySQL", "mysqladmin ping -h localhost --silent"),
            ("rfsim5g-oai-amf", "AMF", "pgrep oai_amf"),
            ("rfsim5g-oai-smf", "SMF", "pgrep oai_smf"),
            ("rfsim5g-oai-upf", "UPF", "pgrep oai_upf")
        ]
        
        for container_name, display_name, check_command in containers:
            logger.info(f"Waiting for {display_name}...")
            if not self.check_container_ready(container_name, display_name, check_command):
                logger.error(f"{display_name} not ready")
                return False
        
        return True
    
    def wait_for_gnb_ready(self) -> bool:
        containers = [
            ("rfsim5g-oai-cucp", "CUCP", "pgrep nr-softmodem"),
            ("rfsim5g-oai-cuup", "CUUP", "pgrep nr-cuup"),
            ("rfsim5g-oai-cuup2", "CUUP2", "pgrep nr-cuup"),
            ("rfsim5g-oai-du", "DU1", "pgrep nr-softmodem"),
            ("rfsim5g-oai-du2", "DU2", "pgrep nr-softmodem"),
            ("rfsim5g-oai-du3", "DU3", "pgrep nr-softmodem")
        ]
        
        for container_name, display_name, check_command in containers:
            logger.info(f"Waiting for {display_name}...")
            if not self.check_container_ready(container_name, display_name, check_command):
                logger.error(f"{display_name} not ready")
                return False
        
        return True
    
    def check_container_ready(self, container_name: str, display_name: str, check_command: str, max_attempts: int = None, wait_time: int = None) -> bool:
        if max_attempts is None:
            max_attempts = self.max_attempts
        if wait_time is None:
            wait_time = self.wait_time
        
        for attempt in range(1, max_attempts + 1):
            try:
                result = subprocess.run(
                    f"docker ps --format '{{{{.Names}}}}' | grep '^{container_name}'",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    logger.debug(f"{display_name} container not found (attempt {attempt}/{max_attempts})")
                    time.sleep(wait_time)
                    continue
                
                result = subprocess.run(
                    f"docker exec {container_name} {check_command}",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info(f"{display_name} is ready!")
                    return True
                
                logger.debug(f"{display_name} not ready yet (attempt {attempt}/{max_attempts})")
                time.sleep(wait_time)
                
            except Exception as e:
                logger.debug(f"Error checking {display_name}: {e}")
                time.sleep(wait_time)
        
        return False
    
    def wait_for_ue_ready(self, container_name: str, ue_name: str, max_attempts: int = None, wait_time: int = None) -> bool:
        if max_attempts is None:
            max_attempts = self.max_attempts
        if wait_time is None:
            wait_time = self.wait_time
        
        for attempt in range(1, max_attempts + 1):
            try:
                result = subprocess.run(
                    f"docker exec {container_name} pgrep nr-uesoftmodem",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    logger.debug(f"{ue_name} process not found (attempt {attempt}/{max_attempts})")
                    time.sleep(wait_time)
                    continue
                
                result = subprocess.run(
                    f"docker exec {container_name} ip addr show dev oaitun_ue1 2>/dev/null | grep 'inet ' | awk '{{print $2}}' | cut -d'/' -f1",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    logger.info(f"{ue_name} is ready with IP {result.stdout.strip()}")
                    return True
                else:
                    logger.debug(f"{ue_name} IP not assigned yet (attempt {attempt}/{max_attempts})")
                    time.sleep(wait_time)
                
            except Exception as e:
                logger.debug(f"Error checking {ue_name}: {e}")
                time.sleep(wait_time)
        
        return False
    
    def start_ue_sequence(self) -> bool:
        ue_containers = [
            ("rfsim5g-oai-nr-ue", "UE1"),
            ("rfsim5g-oai-nr-ue2", "UE2"),
            ("rfsim5g-oai-nr-ue3", "UE3"),
            ("rfsim5g-oai-nr-ue4", "UE4")
        ]
        
        for container, ue_name in ue_containers:
            logger.info(f"Starting {ue_name}...")
            service_name = container.replace('rfsim5g-', '')
            ue_result = self._run_command(f"docker compose up -d {service_name}")
            
            if ue_result['success']:
                if not self.wait_for_ue_ready(container, ue_name):
                    logger.warning(f"{ue_name} not ready, continuing anyway...")
            else:
                logger.error(f"Failed to start {ue_name}")
                return False
        
        return True
    
    def get_ue_ip_address(self, container_name: str) -> Optional[str]:
        try:
            result = self._run_command(f"docker exec {container_name} ip a show oaitun_ue1 2>/dev/null | grep 'inet ' | awk '{{print $2}}' | cut -d'/' -f1")
            if result['success'] and result['stdout'].strip():
                return result['stdout'].strip()
            
            result = self._run_command(f"docker exec {container_name} ip a | grep oaitun | grep 'inet ' | awk '{{print $2}}' | cut -d'/' -f1 | head -1")
            if result['success'] and result['stdout'].strip():
                return result['stdout'].strip()
            
            result = self._run_command(f"docker exec {container_name} ip a | grep 'inet 12.1.1.' | awk '{{print $2}}' | cut -d'/' -f1 | head -1")
            if result['success'] and result['stdout'].strip():
                return result['stdout'].strip()
            
            return None
        except:
            return None
    
    def get_ue_ips_parallel(self, ue_containers: List[str]) -> Dict[str, Optional[str]]:
        results = {}
        threads = []
        
        def get_ip_thread(container_name):
            results[container_name] = self.get_ue_ip_address(container_name)
        
        for container in ue_containers:
            if 'nr-ue' in container:
                thread = threading.Thread(target=get_ip_thread, args=(container,))
                threads.append(thread)
                thread.start()
        
        for thread in threads:
            thread.join(timeout=2)
        
        return results
    
    def test_connectivity(self) -> Dict:
        try:
            ue_containers = {
                'rfsim5g-oai-nr-ue': '12.1.1.2',
                'rfsim5g-oai-nr-ue2': '12.1.1.3',
                'rfsim5g-oai-nr-ue3': '12.1.1.4',
                'rfsim5g-oai-nr-ue4': '12.1.1.5'
            }
            
            actual_ips = {}
            for container, expected_ip in ue_containers.items():
                actual_ip = self.get_ue_ip_address(container)
                if actual_ip:
                    actual_ips[container] = actual_ip
                else:
                    actual_ips[container] = expected_ip
            
            test_results = []
            total_tests = 0
            successful_tests = 0
            failed_tests = 0
            
            for from_container, from_ip in actual_ips.items():
                for to_container, to_ip in actual_ips.items():
                    if from_container != to_container:
                        total_tests += 1
                        
                        ping_result = self._run_command(
                            f"docker exec {from_container} ping -c5 {to_ip}",
                            timeout=30
                        )
                        
                        success = False
                        packet_loss = 'N/A'
                        avg_rtt = 'N/A'
                        details = ''
                        
                        if ping_result['success']:
                            output = ping_result['stdout']
                            
                            if '0% packet loss' in output:
                                success = True
                                packet_loss = '0%'
                            elif 'packet loss' in output:
                                loss_match = re.search(r'(\d+(?:\.\d+)?)% packet loss', output)
                                if loss_match:
                                    packet_loss = f"{loss_match.group(1)}%"
                            
                            rtt_match = re.search(r'rtt min/avg/max/mdev = [\d.]+/([\d.]+)/[\d.]+/[\d.]+ ms', output)
                            if rtt_match:
                                avg_rtt = f"{rtt_match.group(1)}ms"
                            
                            details = f"Ping successful" if success else f"Ping failed"
                        else:
                            details = f"Command failed: {ping_result['stderr']}"
                        
                        from_ue = from_container.replace('rfsim5g-oai-nr-ue', 'UE').replace('rfsim5g-oai-nr-', 'UE')
                        to_ue = to_container.replace('rfsim5g-oai-nr-ue', 'UE').replace('rfsim5g-oai-nr-', 'UE')
                        
                        test_results.append({
                            'from_ue': from_ue,
                            'to_ue': to_ue,
                            'from_container': from_container,
                            'to_container': to_container,
                            'target_ip': to_ip,
                            'success': success,
                            'packet_loss': packet_loss,
                            'avg_rtt': avg_rtt,
                            'details': details
                        })
                        
                        if success:
                            successful_tests += 1
                        else:
                            failed_tests += 1
            
            success_rate = f"{(successful_tests * 100) // total_tests}%" if total_tests > 0 else "0%"
            
            summary = {
                'total': total_tests,
                'successful': successful_tests,
                'failed': failed_tests,
                'success_rate': success_rate
            }
            
            return {
                'success': True,
                'results': test_results,
                'summary': summary,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Connectivity test failed: {e}")
            return {'success': False, 'error': str(e)}


