import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sp5g-graduation-project-2025'
    
    OAI_ROOT = '/home/sp5g/sp5g'
    ADD_ON_ROOT = os.path.join(OAI_ROOT, 'add-on')
    
    NETWORK_NAMESPACES = {
        'core': 'sp5g-core',
        'attacker': 'sp5g-attacker',
        'botnet': 'sp5g-botnet',
        'detector': 'sp5g-detector',
        'defender': 'sp5g-defender'
    }
    
    F1_INTERFACE = {
        'cu_cp_ip': '192.168.71.130',
        'cu_up_ip': '192.168.71.131',
        'du_ip': '192.168.71.132',
        'f1c_port': 38472,
        'f1u_port': 2152
    }
    
    ATTACK_TYPES = {
        'f1c': [
            'massive_ue_connection',
            'ue_context_flooding',
            'handover_flooding',
            'tau_flooding',
            'bearer_flooding',
            'pdu_session_flooding'
        ],
        'f1u': [
            'udp_flood',
            'gtp_flood',
            'data_plane_exhaustion'
        ],
        'advanced': [
            'arp_spoofing',
            'f1ap_fuzzing',
            'slowloris',
            'distributed_ddos'
        ]
    }
    
    DEFENSE_TYPES = {
        'detection': [
            'threshold_based',
            'statistical_analysis',
            'pattern_recognition'
        ],
        'mitigation': [
            'ip_filtering',
            'rate_limiting',
            'dynamic_throttling',
            'du_reconnection',
            'ip_reassignment'
        ]
    }
    
    UE_TYPES = {
        'robot_arm': {
            'name': 'Industrial Robot Arm',
            'criticality': 'critical',
            'latency_req': '1ms',
            'bandwidth': '10Mbps'
        },
        'autonomous_vehicle': {
            'name': 'Autonomous Vehicle',
            'criticality': 'critical',
            'latency_req': '5ms',
            'bandwidth': '50Mbps'
        },
        'military_drone': {
            'name': 'Military Drone',
            'criticality': 'critical',
            'latency_req': '10ms',
            'bandwidth': '100Mbps'
        },
        'smartphone': {
            'name': 'Smartphone',
            'criticality': 'normal',
            'latency_req': '50ms',
            'bandwidth': '20Mbps'
        },
        'broadcast_camera': {
            'name': 'Broadcasting Camera',
            'criticality': 'high',
            'latency_req': '20ms',
            'bandwidth': '200Mbps'
        }
    }
    
    SCENARIOS = {
        'nuclear_plant': {
            'name': 'Nuclear Plant Control',
            'ues': ['robot_arm'],
            'background': 'nuclear_plant.jpg',
            'description': 'Critical infrastructure control scenario'
        },
        'smart_city': {
            'name': 'Smart City Traffic',
            'ues': ['autonomous_vehicle', 'smartphone'],
            'background': 'smart_city.jpg',
            'description': 'Urban autonomous vehicle management'
        },
        'military_ops': {
            'name': 'Military Operation',
            'ues': ['military_drone'],
            'background': 'military.jpg',
            'description': 'Tactical drone operation scenario'
        },
        'public_event': {
            'name': 'Public Event Broadcasting',
            'ues': ['broadcast_camera', 'smartphone'],
            'background': 'public_event.jpg',
            'description': 'Live event broadcasting scenario'
        },
        'residential': {
            'name': 'Residential Smart Home',
            'ues': ['smartphone'],
            'background': 'residential.jpg',
            'description': 'Smart home IoT scenario'
        }
    }
    
    MONITORING_METRICS = {
        'cpu_threshold': 80,
        'memory_threshold': 85,
        'latency_threshold': 100,
        'packet_rate_threshold': 10000,
        'connection_threshold': 1000
    }
    
    PERFORMANCE_COLLECTION_INTERVAL = 1.0
    
    DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
    LOG_DIR = os.path.join(DASHBOARD_DIR, 'logs')
    DATA_DIR = os.path.join(DASHBOARD_DIR, 'data')
    RESULTS_DIR = os.path.join(DASHBOARD_DIR, 'results')



