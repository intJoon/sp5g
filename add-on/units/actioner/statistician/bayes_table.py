#!/usr/bin/env python3

import json
import logging
from datetime import datetime
from typing import Dict, List
from collections import defaultdict

logger = logging.getLogger(__name__)

class BayesTable:
    def __init__(self):
        self.detection_history = []
        self.attack_history = []
        self.confusion_matrix = {
            'true_positive': 0,
            'true_negative': 0,
            'false_positive': 0,
            'false_negative': 0
        }
        self.packet_counts = defaultdict(int)
        
    def record_detection(self, detected: bool, attack_active: bool, packet_count: int):
        timestamp = datetime.now().isoformat()
        
        record = {
            'timestamp': timestamp,
            'detected': detected,
            'attack_active': attack_active,
            'packet_count': packet_count
        }
        
        self.detection_history.append(record)
        self.packet_counts[timestamp] = packet_count
        
        if attack_active and detected:
            self.confusion_matrix['true_positive'] += packet_count
        elif not attack_active and detected:
            self.confusion_matrix['false_positive'] += packet_count
        elif attack_active and not detected:
            self.confusion_matrix['false_negative'] += packet_count
        elif not attack_active and not detected:
            self.confusion_matrix['true_negative'] += packet_count
            
        logger.debug(f"Detection recorded: detected={detected}, attack_active={attack_active}, packets={packet_count}")
    
    def record_attack_start(self, attack_type: str, timestamp: str = None):
        if not timestamp:
            timestamp = datetime.now().isoformat()
            
        self.attack_history.append({
            'timestamp': timestamp,
            'type': attack_type,
            'status': 'started'
        })
        logger.info(f"Attack started: {attack_type} at {timestamp}")
    
    def record_attack_end(self, attack_type: str, timestamp: str = None):
        if not timestamp:
            timestamp = datetime.now().isoformat()
            
        self.attack_history.append({
            'timestamp': timestamp,
            'type': attack_type,
            'status': 'ended'
        })
        logger.info(f"Attack ended: {attack_type} at {timestamp}")
    
    def get_confusion_matrix(self) -> Dict:
        total = sum(self.confusion_matrix.values())
        if total == 0:
            return {
                'matrix': self.confusion_matrix.copy(),
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'false_positive_rate': 0.0,
                'false_negative_rate': 0.0
            }
        
        tp = self.confusion_matrix['true_positive']
        tn = self.confusion_matrix['true_negative']
        fp = self.confusion_matrix['false_positive']
        fn = self.confusion_matrix['false_negative']
        
        accuracy = (tp + tn) / total if total > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        false_positive_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        false_negative_rate = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        
        return {
            'matrix': self.confusion_matrix.copy(),
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'false_positive_rate': false_positive_rate,
            'false_negative_rate': false_negative_rate,
            'total_packets': total
        }
    
    def get_statistics(self) -> Dict:
        return {
            'confusion_matrix': self.get_confusion_matrix(),
            'total_detections': len(self.detection_history),
            'total_attacks': len([a for a in self.attack_history if a['status'] == 'started']),
            'detection_history': self.detection_history[-100:],
            'attack_history': self.attack_history[-50:]
        }
    
    def export_to_json(self, filepath: str):
        data = self.get_statistics()
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Bayes table exported to {filepath}")
    
    def reset(self):
        self.detection_history.clear()
        self.attack_history.clear()
        self.confusion_matrix = {
            'true_positive': 0,
            'true_negative': 0,
            'false_positive': 0,
            'false_negative': 0
        }
        self.packet_counts.clear()
        logger.info("Bayes table reset")

