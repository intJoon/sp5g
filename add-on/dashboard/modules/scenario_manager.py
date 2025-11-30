import os
import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ScenarioManager:
    def __init__(self):
        self.scenarios_root = '/home/sp5g/sp5g/add-on/scenarios'
        self.current_scenario = None
        
        self.scenarios = {
            'nuclear_plant': {
                'name': 'Nuclear Plant Control',
                'description': 'Critical industrial control scenario with robot arms',
                'ues': ['robot_arm'],
                'background': 'nuclear_plant.jpg',
                'attack_impact': {
                    'robot_arm': 'Precision control failure - potential hazardous material exposure'
                },
                'criticality': 'critical'
            },
            'smart_city': {
                'name': 'Smart City Traffic',
                'description': 'Urban autonomous vehicle management',
                'ues': ['autonomous_vehicle', 'smartphone'],
                'background': 'smart_city.jpg',
                'attack_impact': {
                    'autonomous_vehicle': 'Navigation failure - collision risk',
                    'smartphone': 'Communication disruption'
                },
                'criticality': 'high'
            },
            'military_ops': {
                'name': 'Military Operation',
                'description': 'Tactical drone operation scenario',
                'ues': ['military_drone'],
                'background': 'military.jpg',
                'attack_impact': {
                    'military_drone': 'Command & control loss - mission failure'
                },
                'criticality': 'critical'
            },
            'public_event': {
                'name': 'Public Event Broadcasting',
                'description': 'Live event broadcasting with cameras and mobile devices',
                'ues': ['broadcast_camera', 'smartphone'],
                'background': 'public_event.jpg',
                'attack_impact': {
                    'broadcast_camera': 'Live feed interruption',
                    'smartphone': 'Audience communication loss'
                },
                'criticality': 'medium'
            },
            'highway': {
                'name': 'Highway Autonomous Driving',
                'description': 'High-speed autonomous vehicle scenario',
                'ues': ['autonomous_vehicle'],
                'background': 'highway.jpg',
                'attack_impact': {
                    'autonomous_vehicle': 'High-speed navigation failure - catastrophic collision risk'
                },
                'criticality': 'critical'
            }
        }
        
    def load_scenario(self, scenario_id: str) -> Dict:
        try:
            if scenario_id not in self.scenarios:
                return {
                    'status': 'error',
                    'message': f'Unknown scenario: {scenario_id}'
                }
            
            scenario = self.scenarios[scenario_id]
            
            logger.info(f"Loading scenario: {scenario['name']}")
            
            self.current_scenario = {
                'id': scenario_id,
                'config': scenario,
                'loaded_at': datetime.now().isoformat(),
                'ue_states': self._initialize_ue_states(scenario['ues'])
            }
            
            return {
                'status': 'success',
                'message': f"Scenario '{scenario['name']}' loaded successfully",
                'scenario': self.current_scenario
            }
        except Exception as e:
            logger.error(f"Error loading scenario: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_current_scenario(self) -> Dict:
        if self.current_scenario:
            return {
                'status': 'loaded',
                'scenario': self.current_scenario
            }
        return {
            'status': 'none',
            'message': 'No scenario loaded'
        }
    
    def list_scenarios(self) -> List[Dict]:
        return [
            {
                'id': sid,
                'name': s['name'],
                'description': s['description'],
                'criticality': s['criticality'],
                'ue_count': len(s['ues'])
            }
            for sid, s in self.scenarios.items()
        ]
    
    def update_ue_state(self, ue_type: str, state: str) -> Dict:
        try:
            if not self.current_scenario:
                return {
                    'status': 'error',
                    'message': 'No scenario loaded'
                }
            
            if ue_type not in self.current_scenario['ue_states']:
                return {
                    'status': 'error',
                    'message': f'UE type {ue_type} not in current scenario'
                }
            
            self.current_scenario['ue_states'][ue_type]['state'] = state
            self.current_scenario['ue_states'][ue_type]['updated_at'] = datetime.now().isoformat()
            
            return {
                'status': 'success',
                'message': f'UE {ue_type} state updated to {state}',
                'ue_state': self.current_scenario['ue_states'][ue_type]
            }
        except Exception as e:
            logger.error(f"Error updating UE state: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def simulate_attack_impact(self, attack_severity: str) -> Dict:
        try:
            if not self.current_scenario:
                return {
                    'status': 'error',
                    'message': 'No scenario loaded'
                }
            
            scenario = self.current_scenario['config']
            
            impact_results = {}
            
            for ue_type in scenario['ues']:
                impact = scenario['attack_impact'].get(ue_type, 'Service degradation')
                
                if attack_severity == 'critical':
                    state = 'offline'
                    impact_level = 'severe'
                elif attack_severity == 'high':
                    state = 'degraded'
                    impact_level = 'high'
                else:
                    state = 'unstable'
                    impact_level = 'medium'
                
                self.update_ue_state(ue_type, state)
                
                impact_results[ue_type] = {
                    'state': state,
                    'impact': impact,
                    'impact_level': impact_level
                }
            
            return {
                'status': 'success',
                'scenario': scenario['name'],
                'severity': attack_severity,
                'impacts': impact_results
            }
        except Exception as e:
            logger.error(f"Error simulating attack impact: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def simulate_recovery(self) -> Dict:
        try:
            if not self.current_scenario:
                return {
                    'status': 'error',
                    'message': 'No scenario loaded'
                }
            
            for ue_type in self.current_scenario['ue_states']:
                self.update_ue_state(ue_type, 'online')
            
            return {
                'status': 'success',
                'message': 'All UEs recovered to normal state',
                'ue_states': self.current_scenario['ue_states']
            }
        except Exception as e:
            logger.error(f"Error simulating recovery: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _initialize_ue_states(self, ue_types: List[str]) -> Dict:
        states = {}
        
        for ue_type in ue_types:
            states[ue_type] = {
                'type': ue_type,
                'state': 'online',
                'initialized_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        
        return states
    
    def get_ue_definitions(self) -> Dict:
        return {
            'robot_arm': {
                'name': 'Industrial Robot Arm',
                'icon': 'robot',
                'criticality': 'critical',
                'requirements': {
                    'latency': '1ms',
                    'bandwidth': '10Mbps',
                    'reliability': '99.9999%'
                },
                'failure_impact': 'Precision control failure - potential hazardous material exposure'
            },
            'autonomous_vehicle': {
                'name': 'Autonomous Vehicle',
                'icon': 'car',
                'criticality': 'critical',
                'requirements': {
                    'latency': '5ms',
                    'bandwidth': '50Mbps',
                    'reliability': '99.999%'
                },
                'failure_impact': 'Navigation failure - collision risk'
            },
            'military_drone': {
                'name': 'Military Drone',
                'icon': 'drone',
                'criticality': 'critical',
                'requirements': {
                    'latency': '10ms',
                    'bandwidth': '100Mbps',
                    'reliability': '99.999%'
                },
                'failure_impact': 'Command & control loss - mission failure'
            },
            'smartphone': {
                'name': 'Smartphone',
                'icon': 'phone',
                'criticality': 'normal',
                'requirements': {
                    'latency': '50ms',
                    'bandwidth': '20Mbps',
                    'reliability': '99.9%'
                },
                'failure_impact': 'Communication disruption'
            },
            'broadcast_camera': {
                'name': 'Broadcasting Camera',
                'icon': 'camera',
                'criticality': 'high',
                'requirements': {
                    'latency': '20ms',
                    'bandwidth': '200Mbps',
                    'reliability': '99.99%'
                },
                'failure_impact': 'Live feed interruption'
            }
        }



