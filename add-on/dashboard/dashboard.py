import os
import sys
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import Config
from modules.system_manager import SystemManager
from modules.attack_manager import AttackManager
from modules.defense_manager import DefenseManager
from modules.monitoring_manager import MonitoringManager
from modules.scenario_manager import ScenarioManager

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(Config.ADD_ON_ROOT, 'dashboard', 'dashboard.log')),
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

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    emit('connected', {'status': 'ok'})

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

if __name__ == '__main__':
    os.makedirs(Config.LOG_DIR, exist_ok=True)
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    os.makedirs(Config.RESULTS_DIR, exist_ok=True)
    
    logger.info("Starting SP5G Dashboard...")
    logger.info(f"Dashboard available at http://localhost:5000")
    
    start_background_monitoring()
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)


