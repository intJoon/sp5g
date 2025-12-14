import os
import sys
import logging
import signal
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
import time

sys.path.insert(0, os.path.dirname(__file__))

from config import Config
from modules.system_manager import SystemManager
from modules.attack_manager import AttackManager
from modules.defense_manager import DefenseManager
from modules.monitoring_manager import MonitoringManager
from modules.scenario_manager import ScenarioManager

DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, 
            static_folder=os.path.join(DASHBOARD_DIR, 'static'),
            static_url_path='/static',
            template_folder=os.path.join(DASHBOARD_DIR, 'templates'))
app.config.from_object(Config)

DEBUG_MODE = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

CORS(app)
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='threading',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25
)

@app.after_request
def after_request(response):
    if DEBUG_MODE:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

os.makedirs(Config.LOG_DIR, exist_ok=True)
os.makedirs(Config.DATA_DIR, exist_ok=True)
os.makedirs(Config.RESULTS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(Config.LOG_DIR, 'dashboard.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

system_mgr = SystemManager()
attack_mgr = AttackManager()
defense_mgr = DefenseManager()
monitoring_mgr = MonitoringManager()
scenario_mgr = ScenarioManager()

monitoring_thread = None
monitoring_active = False

def start_background_monitoring():
    global monitoring_active, monitoring_thread
    if not monitoring_active:
        monitoring_active = True
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
        logger.info("Background monitoring started automatically")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/landing')
def landing():
    return render_template('landing.html')

@app.route('/api/status')
def get_status():
    try:
        from modules.simple_monitoring import SimpleMonitor
        
        system_status = system_mgr.get_system_status()
        quick_metrics = SimpleMonitor.get_quick_metrics()
        
        status = {
            'system': system_status,
            'network': system_mgr.get_network_status(),
            'monitoring': quick_metrics,
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/config')
def get_config():
    try:
        config = {
            'attack_types': Config.ATTACK_TYPES,
            'defense_types': Config.DEFENSE_TYPES,
            'ue_types': Config.UE_TYPES,
            'scenarios': Config.SCENARIOS,
            'namespaces': Config.NETWORK_NAMESPACES
        }
        return jsonify(config)
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/<action>', methods=['POST'])
def system_action(action):
    try:
        if action == 'start':
            result = system_mgr.start_system()
        elif action == 'stop':
            result = system_mgr.stop_system()
        elif action == 'restart':
            result = system_mgr.restart_system()
        elif action == 'setup_namespaces':
            result = system_mgr.setup_network_namespaces()
        elif action == 'cleanup_namespaces':
            result = system_mgr.cleanup_network_namespaces()
        else:
            return jsonify({'error': f'Unknown action: {action}'}), 400
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in system action {action}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/attack/launch', methods=['POST'])
def launch_attack():
    try:
        data = request.json
        attack_type = data.get('type')
        target = data.get('target')
        params = data.get('params', {})
        mode = data.get('mode', 'manual')
        
        result = attack_mgr.launch_attack(attack_type, target, params, mode)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error launching attack: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/attack/stop', methods=['POST'])
def stop_attack():
    try:
        result = attack_mgr.stop_attack()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error stopping attack: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/defense/enable', methods=['POST'])
def enable_defense():
    try:
        data = request.json
        defense_type = data.get('type')
        params = data.get('params', {})
        
        result = defense_mgr.enable_defense(defense_type, params)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error enabling defense: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/defense/disable', methods=['POST'])
def disable_defense():
    try:
        result = defense_mgr.disable_defense()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error disabling defense: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/scenario/<scenario_id>/load', methods=['POST'])
def load_scenario(scenario_id):
    try:
        result = scenario_mgr.load_scenario(scenario_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error loading scenario: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/start', methods=['POST'])
def start_monitoring():
    global monitoring_active, monitoring_thread
    try:
        if not monitoring_active:
            monitoring_active = True
            monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
            monitoring_thread.start()
            return jsonify({'status': 'started'})
        return jsonify({'status': 'already_running'})
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/stop', methods=['POST'])
def stop_monitoring():
    global monitoring_active
    try:
        monitoring_active = False
        return jsonify({'status': 'stopped'})
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/performance/export', methods=['POST'])
def export_performance():
    try:
        data = request.json
        format_type = data.get('format', 'csv')
        
        result = monitoring_mgr.export_performance_data(format_type)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error exporting performance data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test/connectivity', methods=['POST'])
def test_connectivity():
    try:
        result = system_mgr.test_connectivity()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error testing connectivity: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/source/<category>/<source_type>')
def get_source_code(category, source_type):
    try:
        ADD_ON_ROOT = Config.ADD_ON_ROOT
        source_paths = {
            'attack': {
                'massive_ue_connection': 'units/actioner/attacker/f1c/f1c_attack.py',
                'ue_context_flooding': 'units/actioner/attacker/f1c/f1c_attack.py',
                'handover_flooding': 'units/actioner/attacker/f1c/f1c_attack.py',
                'bearer_flooding': 'units/actioner/attacker/f1c/f1c_attack.py',
                'udp_flood': 'units/actioner/attacker/f1u/f1u_attack.py',
                'gtp_flood': 'units/actioner/attacker/f1u/f1u_attack.py',
                'distributed_ddos': 'units/actioner/attacker/botnet/botnet_controller.py',
                'slowloris': 'units/actioner/attacker/f1c/f1c_attack.py'
            },
            'detection': {
                'threshold_based': 'units/actioner/detector/detector.py',
                'statistical_analysis': 'units/actioner/detector/detector.py',
                'pattern_recognition': 'units/actioner/detector/ml_detector.py'
            },
            'defense': {
                'ip_filtering': 'units/actioner/defender/filter.py',
                'rate_limiting': 'units/actioner/defender/rate_limiter.py',
                'dynamic_throttling': 'units/actioner/defender/rate_limiter.py'
            }
        }
        
        if category not in source_paths or source_type not in source_paths[category]:
            return jsonify({'error': f'Invalid source type: {category}/{source_type}'}), 404
        
        file_path = os.path.join(ADD_ON_ROOT, source_paths[category][source_type])
        
        if not os.path.exists(file_path):
            logger.error(f"Source file not found: {file_path}")
            return jsonify({'error': f'Source file not found: {file_path}'}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        file_name = os.path.basename(file_path)
        relative_path = source_paths[category][source_type]
        
        return jsonify({
            'source_code': source_code,
            'file_name': file_name,
            'file_path': relative_path,
            'type': source_type
        })
    except Exception as e:
        logger.error(f"Error reading source code: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    client_ip = request.remote_addr
    logger.info('Client connected from {} - session ID: {}'.format(client_ip, request.sid))
    emit('connected', {'status': 'ok', 'session_id': request.sid, 'message': 'Welcome to SP5G Dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

@socketio.on('request_update')
def handle_request_update():
    try:
        data = {
            'system': system_mgr.get_system_status(),
            'metrics': monitoring_mgr.get_current_metrics(),
            'timestamp': datetime.now().isoformat()
        }
        emit('status_update', data)
    except Exception as e:
        logger.error(f"Error handling update request: {e}")
        emit('error', {'message': str(e)})

def monitoring_loop():
    global monitoring_active
    logger.info("Monitoring loop started")
    
    from modules.simple_monitoring import SimpleMonitor
    
    while monitoring_active:
        try:
            metrics = SimpleMonitor.get_quick_metrics()
            
            socketio.emit('metrics_update', {
                'metrics': metrics,
                'timestamp': datetime.now().isoformat()
            })
            
            if metrics.get('system', {}).get('cpu_percent', 0) > 80:
                socketio.emit('anomaly_detected', {
                    'type': 'high_cpu',
                    'value': metrics['system']['cpu_percent'],
                    'timestamp': datetime.now().isoformat()
                })
            
            time.sleep(Config.PERFORMANCE_COLLECTION_INTERVAL)
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            time.sleep(1)
    
    logger.info("Monitoring loop stopped")

def signal_handler(sig, frame):
    logger.info(f"Received signal {sig}, shutting down gracefully...")
    global monitoring_active
    monitoring_active = False
    
    if monitoring_thread and monitoring_thread.is_alive():
        logger.info("Waiting for monitoring thread to stop...")
        monitoring_thread.join(timeout=2)
    
    logger.info("Dashboard shutdown complete")
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    os.makedirs(Config.LOG_DIR, exist_ok=True)
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    os.makedirs(Config.RESULTS_DIR, exist_ok=True)
    
    logger.info("Starting SP5G Dashboard...")
    logger.info(f"Dashboard available at http://localhost:5000")
    logger.info(f"Debug mode: {DEBUG_MODE} (set FLASK_DEBUG=False to disable)")
    
    start_background_monitoring()
    
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=DEBUG_MODE, allow_unsafe_werkzeug=True, use_reloader=DEBUG_MODE)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        signal_handler(signal.SIGTERM, None)


