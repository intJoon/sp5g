import psutil
import time
from datetime import datetime

class SimpleMonitor:
    @staticmethod
    def get_quick_metrics():
        try:
            return {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_percent': psutil.cpu_percent(interval=0.1),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': psutil.disk_usage('/').percent,
                    'cpu_count': psutil.cpu_count()
                },
                'network': {
                    'connections': len(psutil.net_connections(kind='inet')),
                    'bytes_sent': psutil.net_io_counters().bytes_sent,
                    'bytes_recv': psutil.net_io_counters().bytes_recv,
                    'packets_sent': psutil.net_io_counters().packets_sent,
                    'packets_recv': psutil.net_io_counters().packets_recv
                },
                'processes': {
                    'gnb_count': len([p for p in psutil.process_iter(['name']) if 'nr-softmodem' in p.info['name']]),
                    'ue_count': len([p for p in psutil.process_iter(['name']) if 'nr-uesoftmodem' in p.info['name']])
                },
                'f1_interface': {
                    'f1c_connections': 0,
                    'f1u_connections': 0,
                    'latency_ms': 0
                }
            }
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

