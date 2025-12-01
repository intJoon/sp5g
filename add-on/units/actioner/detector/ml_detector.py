#!/usr/bin/env python3

import argparse
import sys
import time
import logging
import os
import json
import pickle
import numpy as np
from datetime import datetime
from collections import deque
import psutil

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Install with: pip install scikit-learn")

class MLAttackDetector:
    def __init__(self, model_file=None):
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for ML detection")
        
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
        self.feature_window = deque(maxlen=10)
        self.detection_threshold = 0.7
        
        if model_file and os.path.exists(model_file):
            self.load_model(model_file)
        else:
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        
        logger.info("ML Attack Detector initialized")
    
    def collect_features(self):
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        net_io = psutil.net_io_counters()
        
        connections = len(psutil.net_connections())
        
        features = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'memory_available_mb': memory.available / (1024 * 1024),
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'connection_count': connections
        }
        
        return features
    
    def extract_feature_vector(self, features_dict):
        if self.feature_window:
            prev_features = self.feature_window[-1]
            
            packet_rate = features_dict['packets_recv'] - prev_features.get('packets_recv', 0)
            byte_rate = features_dict['bytes_recv'] - prev_features.get('bytes_recv', 0)
        else:
            packet_rate = 0
            byte_rate = 0
        
        vector = [
            features_dict['cpu_percent'],
            features_dict['memory_percent'],
            features_dict['memory_available_mb'],
            packet_rate,
            byte_rate,
            features_dict['connection_count']
        ]
        
        self.feature_window.append(features_dict)
        
        return np.array(vector).reshape(1, -1)
    
    def generate_training_data(self, normal_samples=500, attack_samples=500):
        logger.info("Generating synthetic training data...")
        
        X = []
        y = []
        
        for _ in range(normal_samples):
            normal_features = [
                np.random.normal(15, 5),
                np.random.normal(25, 5),
                np.random.normal(3000, 500),
                np.random.normal(1000, 200),
                np.random.normal(500000, 100000),
                np.random.normal(100, 20)
            ]
            X.append(normal_features)
            y.append(0)
        
        for _ in range(attack_samples):
            attack_features = [
                np.random.normal(85, 10),
                np.random.normal(75, 10),
                np.random.normal(500, 100),
                np.random.normal(45000, 5000),
                np.random.normal(5000000, 500000),
                np.random.normal(1800, 200)
            ]
            X.append(attack_features)
            y.append(1)
        
        return np.array(X), np.array(y)
    
    def train(self, X=None, y=None, test_size=0.2):
        if X is None or y is None:
            logger.info("No training data provided, generating synthetic data...")
            X, y = self.generate_training_data()
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        logger.info(f"Training with {len(X_train)} samples...")
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        self.model.fit(X_train_scaled, y_train)
        
        y_pred = self.model.predict(X_test_scaled)
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        cm = confusion_matrix(y_test, y_pred)
        
        logger.info("="*60)
        logger.info("Training Complete - Model Performance")
        logger.info("="*60)
        logger.info(f"Accuracy:  {accuracy*100:.2f}%")
        logger.info(f"Precision: {precision*100:.2f}%")
        logger.info(f"Recall:    {recall*100:.2f}%")
        logger.info(f"F1-Score:  {f1*100:.2f}%")
        logger.info("")
        logger.info("Confusion Matrix:")
        logger.info(f"  TN: {cm[0][0]}  FP: {cm[0][1]}")
        logger.info(f"  FN: {cm[1][0]}  TP: {cm[1][1]}")
        logger.info("="*60)
        
        self.is_trained = True
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'confusion_matrix': cm.tolist()
        }
    
    def predict(self, features_vector=None):
        if not self.is_trained:
            logger.error("Model is not trained yet")
            return None
        
        if features_vector is None:
            features_dict = self.collect_features()
            features_vector = self.extract_feature_vector(features_dict)
        
        features_scaled = self.scaler.transform(features_vector)
        
        prediction = self.model.predict(features_scaled)[0]
        probability = self.model.predict_proba(features_scaled)[0]
        
        result = {
            'is_attack': bool(prediction),
            'confidence': float(probability[1]),
            'prediction': 'ATTACK' if prediction == 1 else 'NORMAL',
            'timestamp': datetime.now().isoformat()
        }
        
        return result
    
    def monitor_realtime(self, duration=60, interval=1):
        if not self.is_trained:
            logger.error("Model must be trained before monitoring")
            return
        
        logger.info(f"Starting real-time monitoring for {duration}s...")
        logger.info("="*80)
        
        start_time = time.time()
        detections = []
        
        try:
            while (time.time() - start_time) < duration:
                result = self.predict()
                
                if result['is_attack'] and result['confidence'] > self.detection_threshold:
                    logger.warning(f"⚠️  ATTACK DETECTED! Confidence: {result['confidence']*100:.1f}%")
                    detections.append(result)
                else:
                    logger.info(f"✓ Normal traffic (confidence: {(1-result['confidence'])*100:.1f}%)")
                
                time.sleep(interval)
        
        except KeyboardInterrupt:
            logger.info("\nMonitoring stopped by user")
        
        logger.info("="*80)
        logger.info(f"Monitoring complete. Detected {len(detections)} attacks")
        
        return detections
    
    def save_model(self, filepath='ml_model.pkl'):
        if not self.is_trained:
            logger.error("Model is not trained yet")
            return False
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'threshold': self.detection_threshold,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {filepath}")
        return True
    
    def load_model(self, filepath):
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.detection_threshold = model_data.get('threshold', 0.7)
        self.is_trained = True
        
        logger.info(f"Model loaded from {filepath}")
        return True
    
    def get_feature_importance(self):
        if not self.is_trained:
            logger.error("Model is not trained yet")
            return None
        
        feature_names = [
            'CPU %',
            'Memory %',
            'Available Memory (MB)',
            'Packet Rate',
            'Byte Rate',
            'Connections'
        ]
        
        importances = self.model.feature_importances_
        
        importance_dict = {
            name: float(imp) 
            for name, imp in zip(feature_names, importances)
        }
        
        logger.info("Feature Importance:")
        for name, imp in sorted(importance_dict.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {name:25}: {imp*100:.2f}%")
        
        return importance_dict

def main():
    parser = argparse.ArgumentParser(description='ML-based Attack Detector')
    parser.add_argument('--train', '-t', action='store_true', help='Train the model')
    parser.add_argument('--monitor', '-m', action='store_true', help='Real-time monitoring')
    parser.add_argument('--duration', '-d', type=int, default=60, help='Monitoring duration (seconds)')
    parser.add_argument('--model', '-M', default='ml_model.pkl', help='Model file path')
    parser.add_argument('--samples', '-s', type=int, default=1000, help='Training samples per class')
    
    args = parser.parse_args()
    
    if not SKLEARN_AVAILABLE:
        logger.error("Please install scikit-learn: pip install scikit-learn")
        sys.exit(1)
    
    detector = MLAttackDetector(model_file=args.model if not args.train else None)
    
    if args.train:
        logger.info("="*80)
        logger.info("ML ATTACK DETECTOR - Training Mode")
        logger.info("="*80)
        
        detector.train()
        detector.save_model(args.model)
        detector.get_feature_importance()
    
    if args.monitor:
        if not detector.is_trained:
            logger.error("Model not trained. Please train first with --train")
            sys.exit(1)
        
        logger.info("="*80)
        logger.info("ML ATTACK DETECTOR - Monitoring Mode")
        logger.info("="*80)
        
        detections = detector.monitor_realtime(duration=args.duration)
        
        if detections:
            logger.info(f"\nDetected attacks:")
            for det in detections:
                logger.info(f"  {det['timestamp']}: {det['confidence']*100:.1f}% confidence")
    
    if not args.train and not args.monitor:
        logger.error("Please specify --train or --monitor")
        parser.print_help()

if __name__ == '__main__':
    main()

