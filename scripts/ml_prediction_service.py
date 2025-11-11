#!/usr/bin/env python3
"""
ML Prediction Service - Phase 4.3
Automatic 5-minute prediction update loop for continuous ML predictions
"""

import time
import json
import logging
import threading
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from scripts.ml_autoscaler import MLAutoScaler
from scripts.ml_ensemble import EnsemblePredictor
from scripts.ml_data_collector import MLDataCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLPredictionService:
    """Continuous ML prediction service with 5-minute update intervals"""
    
    def __init__(self):
        self.ml_autoscaler = MLAutoScaler()
        self.ensemble = EnsemblePredictor()
        self.data_collector = MLDataCollector()
        
        # Service configuration
        self.update_interval = 300  # 5 minutes in seconds
        self.predictions_file = "dashboard-data/ml_predictions.json"
        self.service_status_file = "dashboard-data/ml_service_status.json"
        
        # Service state
        self.running = False
        self.last_update = None
        self.prediction_count = 0
        self.error_count = 0
        
        # Threading
        self.prediction_thread = None
        self.stop_event = threading.Event()
        
    def start_service(self):
        """Start the continuous prediction service"""
        if self.running:
            logger.warning("Prediction service already running")
            return
        
        logger.info("Starting ML Prediction Service with 5-minute intervals")
        self.running = True
        self.stop_event.clear()
        
        # Start prediction thread
        self.prediction_thread = threading.Thread(target=self._prediction_loop, daemon=True)
        self.prediction_thread.start()
        
        # Update service status
        self._update_service_status("running")
        
    def stop_service(self):
        """Stop the continuous prediction service"""
        if not self.running:
            logger.warning("Prediction service not running")
            return
        
        logger.info("Stopping ML Prediction Service")
        self.running = False
        self.stop_event.set()
        
        if self.prediction_thread:
            self.prediction_thread.join(timeout=10)
        
        # Update service status
        self._update_service_status("stopped")
        
    def _prediction_loop(self):
        """Main prediction loop running every 5 minutes"""
        logger.info("ML Prediction loop started")
        
        while not self.stop_event.is_set():
            try:
                # Run prediction update
                self._update_predictions()
                
                # Wait for next interval or stop signal
                if self.stop_event.wait(timeout=self.update_interval):
                    break  # Stop signal received
                    
            except Exception as e:
                self.error_count += 1
                logger.error(f"Error in prediction loop: {e}")
                # Continue running despite errors
                
        logger.info("ML Prediction loop stopped")
        
    def _update_predictions(self):
        """Update predictions for all ML policies"""
        try:
            start_time = datetime.now()
            logger.info("Starting prediction update cycle")
            
            # Get all ML policies
            policies = self.ml_autoscaler.load_ml_policies()
            enabled_policies = [p for p in policies if p.get('enabled', False)]
            
            if not enabled_policies:
                logger.info("No enabled ML policies found")
                return
            
            predictions_batch = []
            
            # Generate predictions for each enabled policy
            for policy in enabled_policies:
                try:
                    app_name = policy['application']
                    horizons = policy.get('prediction_horizons', [15, 30, 60])
                    
                    # Get current metrics
                    current_data = self.ml_autoscaler.get_current_enhanced_metrics(app_name)
                    if not current_data:
                        # Suppress repetitive warnings - only log once per hour per app
                        continue
                    
                    # Generate multi-horizon predictions
                    prediction = self.ensemble.predict_multi_horizon(app_name, current_data, horizons)
                    
                    # Add policy context
                    prediction['policy'] = {
                        'application': app_name,
                        'horizons': horizons,
                        'confidence_threshold': policy.get('confidence_threshold', 75)
                    }
                    
                    predictions_batch.append(prediction)
                    
                except Exception as e:
                    logger.error(f"Error generating prediction for {policy.get('application', 'unknown')}: {e}")
            
            # Save predictions batch
            if predictions_batch:
                self._save_predictions_batch(predictions_batch)
                self.prediction_count += len(predictions_batch)
            
            # Update service status
            self.last_update = start_time.isoformat()
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Prediction update completed: {len(predictions_batch)} predictions in {duration:.2f}s")
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error in prediction update: {e}")
            
    def _save_predictions_batch(self, predictions: List[Dict]):
        """Save batch of predictions to database"""
        try:
            from scripts.database_manager import DatabaseManager
            db = DatabaseManager()
            
            # Flatten predictions for database storage
            db_predictions = []
            for pred in predictions:
                app_name = pred['policy']['application']
                for horizon, data in pred.get('predictions', {}).items():
                    if isinstance(data, dict):
                        db_predictions.append({
                            'application': app_name,
                            'horizon_minutes': int(horizon.replace('m', '')),
                            'predicted_cpu': data.get('cpu_predicted', 0),
                            'predicted_memory': data.get('memory_predicted', 0),
                            'predicted_replicas': data.get('predicted_replicas', 1),
                            'confidence': data.get('confidence', 0),
                            'model_used': data.get('model', 'ensemble'),
                            'timestamp': datetime.now().isoformat()
                        })
            
            if db_predictions:
                db.save_ml_predictions(db_predictions)
                
        except Exception as e:
            logger.error(f"Error saving predictions batch: {e}")
            
    def _load_predictions(self) -> List[Dict]:
        """Load existing predictions from database"""
        try:
            from scripts.database_manager import DatabaseManager
            db = DatabaseManager()
            return db.get_recent_ml_predictions(hours=24)
        except Exception as e:
            logger.error(f"Error loading predictions: {e}")
            return []
            
    def _update_service_status(self, status: str):
        """Update service status file"""
        try:
            status_data = {
                'status': status,
                'last_update': self.last_update,
                'prediction_count': self.prediction_count,
                'error_count': self.error_count,
                'update_interval': self.update_interval,
                'started_at': datetime.now().isoformat() if status == 'running' else None
            }
            
            with open(self.service_status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating service status: {e}")
            
    def get_service_status(self) -> Dict:
        """Get current service status"""
        try:
            with open(self.service_status_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'status': 'stopped', 'error': 'Status file not found'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
            
    def get_recent_predictions(self, hours: int = 1) -> List[Dict]:
        """Get recent predictions within specified hours"""
        try:
            from scripts.database_manager import DatabaseManager
            db = DatabaseManager()
            return db.get_recent_ml_predictions(hours=hours)
        except Exception as e:
            logger.error(f"Error getting recent predictions: {e}")
            return []
            
    def force_prediction_update(self) -> Dict:
        """Force immediate prediction update (for testing/manual trigger)"""
        try:
            logger.info("Force prediction update triggered")
            self._update_predictions()
            return {'success': True, 'message': 'Prediction update completed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

def main():
    """Main function for running the service"""
    service = MLPredictionService()
    
    try:
        # Start the service
        service.start_service()
        
        # Keep main thread alive
        logger.info("ML Prediction Service running. Press Ctrl+C to stop.")
        while service.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
    finally:
        service.stop_service()
        logger.info("ML Prediction Service stopped")

def test_prediction_service():
    """Test the prediction service"""
    service = MLPredictionService()
    
    print("Testing ML Prediction Service...")
    
    # Test service status
    print("\n1. Initial Service Status:")
    status = service.get_service_status()
    print(f"   Status: {status}")
    
    # Test force update
    print("\n2. Force Prediction Update:")
    result = service.force_prediction_update()
    print(f"   Result: {result}")
    
    # Test recent predictions
    print("\n3. Recent Predictions:")
    recent = service.get_recent_predictions(1)
    print(f"   Found {len(recent)} recent prediction batches")
    
    # Test service start/stop
    print("\n4. Testing Service Start/Stop:")
    service.start_service()
    time.sleep(2)  # Let it run briefly
    service.stop_service()
    print("   Service start/stop completed")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_prediction_service()
    else:
        main()