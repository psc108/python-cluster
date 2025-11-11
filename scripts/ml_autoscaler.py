#!/usr/bin/env python3
"""
ML-Enhanced Auto-Scaler - Phase 4 Integration
Integrates ML predictions with existing auto-scaling system
"""

import time
import json
import requests
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from scripts.ml_ensemble import EnsemblePredictor
from scripts.ml_data_collector import MLDataCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLAutoScaler:
    """ML-enhanced auto-scaler with predictive capabilities"""
    
    def __init__(self):
        self.dashboard_api = "http://localhost:8080/api/cluster.php"
        self.ensemble = EnsemblePredictor()
        self.data_collector = MLDataCollector()
        
        # ML-specific settings
        self.ml_policies_file = "dashboard-data/ml_scaling_policies.json"
        self.ml_events_file = "dashboard-data/ml_scaling_events.json"
        self.ml_config_file = "dashboard-data/ml_configuration.json"
        self.training_interval = 3600  # Retrain every hour
        self.last_training = {}
        self.default_horizons = [15, 30, 60]  # Multi-horizon predictions
        
        # Cooldown tracking
        self.last_ml_scaling = {}
        self.ml_cooldown = 600  # 10 minutes between ML scaling actions
        
        # Load ML configuration
        self.load_ml_configuration()
        
    def create_ml_policy(self, app_name: str, config: Dict) -> Dict:
        """Create new ML-based scaling policy with advanced configuration"""
        policy = {
            'application': app_name,
            'enabled': True,
            'type': 'ml_predictive_proactive',
            'created_at': datetime.now().isoformat(),
            'prediction_horizons': config.get('prediction_horizons', self.default_horizons),
            'primary_horizon': config.get('primary_horizon', 30),
            'confidence_threshold': config.get('confidence_threshold', 75),
            'cpu_scale_up_threshold': config.get('cpu_scale_up_threshold', 75),
            'memory_scale_up_threshold': config.get('memory_scale_up_threshold', 80),
            'cpu_scale_down_threshold': config.get('cpu_scale_down_threshold', 30),
            'memory_scale_down_threshold': config.get('memory_scale_down_threshold', 40),
            'min_replicas': config.get('min_replicas', 1),
            'max_replicas': config.get('max_replicas', 10),
            'scale_increment': config.get('scale_increment', 1),
            'scale_decrement': config.get('scale_decrement', 1),
            # Advanced configuration
            'model_weights': config.get('model_weights', {
                'linear_trend': 0.3,
                'seasonal_pattern': 0.4,
                'anomaly_detection': 0.3
            }),
            'auto_retrain': config.get('auto_retrain', True),
            'retrain_interval_hours': config.get('retrain_interval_hours', 24),
            'data_retention_days': config.get('data_retention_days', 30),
            'min_data_points': config.get('min_data_points', 1000),
            # Proactive scaling configuration
            'proactive_scaling': config.get('proactive_scaling', True),
            'look_ahead_minutes': config.get('look_ahead_minutes', 30)
        }
        
        # Update ensemble with custom weights if provided
        if 'model_weights' in config:
            weight_result = self.ensemble.update_model_weights(config['model_weights'])
            if not weight_result.get('success'):
                return {'success': False, 'error': weight_result.get('error')}
        
        # Save policy
        policies = self.load_ml_policies()
        policies = [p for p in policies if p.get('application') != app_name]
        policies.append(policy)
        self.save_ml_policies(policies)
        
        return {'success': True, 'policy': policy}
    
    def load_ml_policies(self) -> List[Dict]:
        """Load ML-based scaling policies from database"""
        try:
            from scripts.database_manager import DatabaseManager
            db = DatabaseManager()
            return db.get_ml_policies()
        except Exception:
            return []
    
    def save_ml_policies(self, policies: List[Dict]):
        """Save ML policies to database"""
        try:
            from scripts.database_manager import DatabaseManager
            db = DatabaseManager()
            for policy in policies:
                db.save_ml_policy(policy)
        except Exception:
            pass
    
    def evaluate_ml_policies(self) -> List[Dict]:
        """Evaluate all ML-based policies"""
        policies = self.load_ml_policies()
        actions = []
        
        for policy in policies:
            if policy.get('enabled', False):
                try:
                    action = self.evaluate_ml_policy(policy)
                    if action:
                        actions.append(action)
                except Exception as e:
                    logger.error(f"Error evaluating ML policy: {e}")
        
        return actions
    
    def evaluate_ml_policy(self, policy: Dict) -> Optional[Dict]:
        """Evaluate single ML policy with auto-retraining"""
        app_name = policy['application']
        
        # Check cooldown
        if self.is_in_ml_cooldown(app_name):
            return None
        
        # Check if auto-retraining is needed
        if policy.get('auto_retrain', True):
            retrain_result = self.ensemble.auto_retrain_models(app_name)
            if retrain_result.get('retrained'):
                logger.info(f"Auto-retrained models for {app_name}: {retrain_result}")
        
        # Update ensemble weights if policy has custom weights
        if 'model_weights' in policy:
            self.ensemble.update_model_weights(policy['model_weights'])
        
        # Get current metrics
        current_data = self.get_current_enhanced_metrics(app_name)
        if not current_data:
            return None
        
        # Get ML recommendation with multi-horizon analysis
        horizons = policy.get('prediction_horizons', self.default_horizons)
        recommendation = self.ensemble.get_scaling_recommendation(app_name, current_data, policy, horizons)
        
        if recommendation:
            success = self.execute_ml_scaling(recommendation, policy)
            if success:
                self.last_ml_scaling[app_name] = time.time()
                return recommendation
        
        return None
    
    def get_current_enhanced_metrics(self, app_name: str) -> Optional[Dict]:
        """Get current metrics with ML features"""
        try:
            response = requests.get(f"{self.dashboard_api}?action=applications", timeout=10)
            if response.status_code != 200:
                return None
            
            apps = response.json()
            for app in apps:
                if app['name'] == app_name and app.get('status') == 'running':
                    return self.data_collector.enhance_app_metrics(app)
            
            return None
            
        except Exception as e:
            # Suppress repetitive database connection errors
            return None
    
    def execute_ml_scaling(self, recommendation: Dict, policy: Dict) -> bool:
        """Execute ML-based scaling action"""
        try:
            app_name = policy['application']
            target_replicas = recommendation['target_replicas']
            
            response = requests.post(f"{self.dashboard_api}?action=scale", 
                                   json={
                                       'application': app_name,
                                       'replicas': target_replicas
                                   }, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    # Log multi-horizon scaling event
                    self.log_ml_scaling_event(recommendation, policy)
                    logger.info(f"ML multi-horizon scaling executed: {app_name} -> {target_replicas}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing ML scaling: {e}")
            return False
    
    def log_ml_scaling_event(self, recommendation: Dict, policy: Dict):
        """Log ML scaling event with multi-horizon details"""
        try:
            event = {
                'timestamp': datetime.now().isoformat(),
                'application': policy['application'],
                'action': recommendation['action'],
                'from_replicas': recommendation['current_replicas'],
                'to_replicas': recommendation['target_replicas'],
                'reason': recommendation['reason'],
                'confidence': recommendation['confidence'],
                'type': 'ml_predictive_multi_horizon',
                'horizon_analysis': recommendation.get('horizon_analysis', {}),
                'policy_horizons': policy.get('prediction_horizons', self.default_horizons)
            }
            
            # Save to ML events file
            events = self.load_ml_events()
            events.append(event)
            # Keep only last 100 events
            events = events[-100:]
            self.save_ml_events(events)
            
        except Exception as e:
            logger.error(f"Error logging ML scaling event: {e}")
    
    def load_ml_events(self) -> List[Dict]:
        """Load ML scaling events from database"""
        try:
            from scripts.database_manager import DatabaseManager
            db = DatabaseManager()
            return db.get_ml_scaling_events()
        except Exception:
            return []
    
    def save_ml_events(self, events: List[Dict]):
        """Save ML events to database"""
        try:
            from scripts.database_manager import DatabaseManager
            db = DatabaseManager()
            for event in events:
                db.log_ml_scaling_event(event)
        except Exception:
            pass
    
    def is_in_ml_cooldown(self, app_name: str) -> bool:
        """Check if application is in ML scaling cooldown"""
        if app_name not in self.last_ml_scaling:
            return False
        return (time.time() - self.last_ml_scaling[app_name]) < self.ml_cooldown
    
    def load_ml_configuration(self):
        """Load ML system configuration"""
        try:
            if os.path.exists(self.ml_config_file):
                with open(self.ml_config_file, 'r') as f:
                    config = json.load(f)
                    
                # Update ensemble configuration
                if 'retrain_interval_hours' in config:
                    self.ensemble.retrain_interval = config['retrain_interval_hours'] * 3600
                if 'data_retention_days' in config:
                    self.ensemble.data_retention = config['data_retention_days'] * 24 * 3600
                if 'min_data_points' in config:
                    self.ensemble.min_data_points = config['min_data_points']
                    
        except Exception as e:
            logger.error(f"Error loading ML configuration: {e}")
    
    def save_ml_configuration(self, config: Dict):
        """Save ML system configuration"""
        try:
            with open(self.ml_config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving ML configuration: {e}")
    
    def update_ml_configuration(self, config: Dict) -> Dict:
        """Update ML system configuration"""
        try:
            # Validate configuration
            valid_keys = ['retrain_interval_hours', 'data_retention_days', 'min_data_points', 'default_model_weights']
            for key in config:
                if key not in valid_keys:
                    return {'success': False, 'error': f'Invalid configuration key: {key}'}
            
            # Update ensemble settings
            if 'retrain_interval_hours' in config:
                self.ensemble.retrain_interval = config['retrain_interval_hours'] * 3600
            if 'data_retention_days' in config:
                self.ensemble.data_retention = config['data_retention_days'] * 24 * 3600
            if 'min_data_points' in config:
                self.ensemble.min_data_points = config['min_data_points']
            if 'default_model_weights' in config:
                weight_result = self.ensemble.update_model_weights(config['default_model_weights'])
                if not weight_result.get('success'):
                    return weight_result
            
            # Save configuration
            self.save_ml_configuration(config)
            
            return {'success': True, 'config': config}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_ml_status(self) -> Dict:
        """Get ML auto-scaler status with configuration info"""
        policies = self.load_ml_policies()
        model_status = self.ensemble.get_model_status()
        
        # Analyze horizon usage
        horizon_usage = {}
        auto_retrain_enabled = 0
        custom_weights_count = 0
        
        for policy in policies:
            horizons = policy.get('prediction_horizons', self.default_horizons)
            for h in horizons:
                horizon_usage[f'{h}m'] = horizon_usage.get(f'{h}m', 0) + 1
            
            if policy.get('auto_retrain', True):
                auto_retrain_enabled += 1
            if 'model_weights' in policy:
                custom_weights_count += 1
        
        # Get prediction service status
        prediction_service_status = self.get_prediction_service_status()
        
        return {
            'ml_policies': len(policies),
            'enabled_policies': len([p for p in policies if p.get('enabled')]),
            'auto_retrain_enabled': auto_retrain_enabled,
            'custom_weights_count': custom_weights_count,
            'model_status': model_status,
            'default_horizons': self.default_horizons,
            'horizon_usage': horizon_usage,
            'multi_horizon_enabled': True,
            'prediction_service': prediction_service_status,
            'automatic_updates': prediction_service_status.get('status') == 'running',
            'configuration': {
                'retrain_interval_hours': self.ensemble.retrain_interval / 3600,
                'data_retention_days': self.ensemble.data_retention / (24 * 3600),
                'min_data_points': self.ensemble.min_data_points
            },
            'proactive_scaling': True,
            'default_look_ahead_minutes': 30
        }
    
    def get_multi_horizon_predictions(self, app_name: str, horizons: List[int] = None) -> Dict:
        """Get multi-horizon predictions for an application"""
        if horizons is None:
            horizons = self.default_horizons
        
        current_data = self.get_current_enhanced_metrics(app_name)
        if not current_data:
            return {'error': 'Unable to get current metrics'}
        
        return self.ensemble.predict_multi_horizon(app_name, current_data, horizons)
    
    def start_prediction_service(self) -> Dict:
        """Start the automatic 5-minute prediction service"""
        try:
            from scripts.ml_prediction_service import MLPredictionService
            
            # Check if service is already running
            service = MLPredictionService()
            status = service.get_service_status()
            
            if status.get('status') == 'running':
                return {'success': False, 'message': 'Prediction service already running'}
            
            # Start the service
            service.start_service()
            return {'success': True, 'message': 'Prediction service started'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop_prediction_service(self) -> Dict:
        """Stop the automatic prediction service"""
        try:
            from scripts.ml_prediction_service import MLPredictionService
            
            service = MLPredictionService()
            service.stop_service()
            return {'success': True, 'message': 'Prediction service stopped'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_prediction_service_status(self) -> Dict:
        """Get prediction service status"""
        try:
            from scripts.ml_prediction_service import MLPredictionService
            
            service = MLPredictionService()
            return service.get_service_status()
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

def test_ml_autoscaler():
    """Test the ML auto-scaler with configurable weights and auto-retraining"""
    ml_scaler = MLAutoScaler()
    
    print("Testing ML Auto-Scaler with Configurable Weights and Auto-Retraining...")
    
    # Test policy creation with custom weights and auto-retraining
    config = {
        'prediction_horizons': [15, 30, 60],
        'primary_horizon': 30,
        'confidence_threshold': 70,
        'cpu_scale_up_threshold': 75,
        'cpu_scale_down_threshold': 30,
        'min_replicas': 1,
        'max_replicas': 5,
        'model_weights': {
            'linear_trend': 0.5,
            'seasonal_pattern': 0.3,
            'anomaly_detection': 0.2
        },
        'auto_retrain': True,
        'retrain_interval_hours': 12,
        'data_retention_days': 14,
        'min_data_points': 500
    }
    
    print("\n1. Creating ML Policy with Custom Configuration:")
    result = ml_scaler.create_ml_policy('test-app', config)
    print(f"   Result: {result}")
    
    # Test configuration update
    print("\n2. Testing Configuration Update:")
    new_config = {
        'retrain_interval_hours': 6,
        'data_retention_days': 21,
        'min_data_points': 750
    }
    config_result = ml_scaler.update_ml_configuration(new_config)
    print(f"   Config Update Result: {config_result}")
    
    # Test multi-horizon predictions
    print("\n3. Testing Multi-Horizon Predictions:")
    predictions = ml_scaler.get_multi_horizon_predictions('test-app', [15, 30, 60])
    print(f"   Result: {predictions}")
    
    # Test enhanced status with configuration info
    print("\n4. Enhanced ML Status:")
    status = ml_scaler.get_ml_status()
    print(f"   Result: {status}")

def main():
    """Continuous ML auto-scaling loop"""
    ml_scaler = MLAutoScaler()
    
    print("ML Auto-Scaler - Continuous Mode")
    print("Evaluating ML policies every 60 seconds...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            # Evaluate all ML policies
            actions = ml_scaler.evaluate_ml_policies()
            
            if actions:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Executed {len(actions)} ML scaling actions")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] No ML scaling actions needed")
            
            # Wait 60 seconds
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\nML Auto-Scaler stopped")
    except Exception as e:
        print(f"Error in ML auto-scaler loop: {e}")
        time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_ml_autoscaler()
    else:
        main()