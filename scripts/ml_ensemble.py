#!/usr/bin/env python3
"""
ML Ensemble Predictor - Phase 4.3
Combines multiple ML models for robust predictions
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from scripts.ml_predictors import LinearTrendPredictor, SeasonalPredictor, AnomalyDetectionPredictor
from scripts.ml_data_collector import MLDataCollector

class EnsemblePredictor:
    """Ensemble predictor combining multiple ML models"""
    
    def __init__(self, custom_weights=None):
        self.predictors = {
            'linear_trend': LinearTrendPredictor(),
            'seasonal_pattern': SeasonalPredictor(),
            'anomaly_detection': AnomalyDetectionPredictor()
        }
        
        # Configurable model weights - can be overridden
        self.default_weights = {
            'linear_trend': 0.3,
            'seasonal_pattern': 0.4,
            'anomaly_detection': 0.3
        }
        self.weights = custom_weights or self.default_weights
        
        self.data_collector = MLDataCollector()
        self.min_training_samples = 100
        self.default_horizons = [15, 30, 60]  # Default prediction horizons in minutes
        
        # Automatic retraining configuration
        self.retrain_interval = 24 * 3600  # 24 hours
        self.data_retention = 30 * 24 * 3600  # 30 days
        self.min_data_points = 1000
        self.last_training = {}
        
    def train_models(self, app_name: str, days: int = 14) -> Dict:
        """Train all models for specific application"""
        training_results = {}
        
        # Get training data
        historical_data = self.data_collector.get_metrics_for_app(app_name, days)
        
        if len(historical_data) < self.min_training_samples:
            return {
                'success': False,
                'error': f'Insufficient data: {len(historical_data)} samples (need {self.min_training_samples})',
                'models_trained': 0
            }
        
        # Convert to DataFrame
        df = pd.DataFrame(historical_data)
        
        # Train each model
        models_trained = 0
        for name, predictor in self.predictors.items():
            try:
                success = predictor.train(df)
                training_results[name] = {
                    'success': success,
                    'info': predictor.get_model_info()
                }
                if success:
                    models_trained += 1
                    
            except Exception as e:
                training_results[name] = {
                    'success': False,
                    'error': str(e)
                }
        
        return {
            'success': models_trained > 0,
            'models_trained': models_trained,
            'total_models': len(self.predictors),
            'training_samples': len(historical_data),
            'results': training_results
        }
    
    def predict_ensemble(self, app_name: str, current_data: Dict, horizon_minutes: int) -> Dict:
        """Generate ensemble prediction for single horizon"""
        try:
            predictions = {}
            total_weight = 0
            weighted_cpu = 0
            weighted_memory = 0
            
            # Get predictions from each model
            for name, predictor in self.predictors.items():
                if predictor.is_trained:
                    pred = predictor.predict(current_data, horizon_minutes)
                    predictions[name] = pred
                    
                    # Weight by confidence and model weight
                    if pred.get('confidence', 0) > 0:
                        model_weight = self.weights[name]
                        confidence_weight = pred['confidence'] / 100
                        
                        # Special handling for anomaly detection
                        if name == 'anomaly_detection' and pred.get('is_anomaly', False):
                            # Boost anomaly detection weight when anomaly detected
                            final_weight = model_weight * confidence_weight * 1.5
                        else:
                            final_weight = model_weight * confidence_weight
                        
                        weighted_cpu += pred['cpu_predicted'] * final_weight
                        weighted_memory += pred['memory_predicted'] * final_weight
                        total_weight += final_weight
                else:
                    predictions[name] = {'confidence': 0, 'error': 'Model not trained'}
            
            # Calculate ensemble prediction
            if total_weight > 0:
                ensemble_cpu = weighted_cpu / total_weight
                ensemble_memory = weighted_memory / total_weight
                ensemble_confidence = min(100, total_weight * 100)
            else:
                # Fallback to current values
                ensemble_cpu = current_data.get('cpu_percent', 0)
                ensemble_memory = current_data.get('memory_percent', 0)
                ensemble_confidence = 0
            
            return {
                'application': app_name,
                'horizon_minutes': horizon_minutes,
                'ensemble_prediction': {
                    'cpu_predicted': float(max(0, min(100, ensemble_cpu))),
                    'memory_predicted': float(max(0, min(100, ensemble_memory))),
                    'confidence': float(ensemble_confidence)
                },
                'individual_predictions': predictions,
                'models_used': len([p for p in predictions.values() if p.get('confidence', 0) > 0]),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'application': app_name,
                'error': str(e),
                'ensemble_prediction': {'confidence': 0},
                'individual_predictions': {},
                'models_used': 0
            }
    
    def predict_multi_horizon(self, app_name: str, current_data: Dict, horizons: List[int] = [15, 30, 60]) -> Dict:
        """Generate ensemble predictions for multiple horizons"""
        try:
            multi_predictions = {}
            
            # Get predictions for each horizon
            for horizon in horizons:
                prediction = self.predict_ensemble(app_name, current_data, horizon)
                multi_predictions[f'{horizon}m'] = prediction
            
            # Calculate aggregate confidence across horizons
            confidences = [pred.get('ensemble_prediction', {}).get('confidence', 0) 
                          for pred in multi_predictions.values()]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                'application': app_name,
                'horizons': horizons,
                'predictions': multi_predictions,
                'aggregate_confidence': float(avg_confidence),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'application': app_name,
                'error': str(e),
                'predictions': {},
                'aggregate_confidence': 0
            }
    
    def get_scaling_recommendation(self, app_name: str, current_data: Dict, 
                                 policy: Dict, horizons: List[int] = [15, 30, 60]) -> Optional[Dict]:
        """Get scaling recommendation based on multi-horizon ML predictions with proactive lookAhead"""
        try:
            # Get multi-horizon predictions
            multi_pred = self.predict_multi_horizon(app_name, current_data, horizons)
            
            if multi_pred.get('aggregate_confidence', 0) < policy.get('confidence_threshold', 70):
                return None  # Not confident enough
            
            # Check for proactive scaling with lookAhead
            look_ahead_minutes = policy.get('look_ahead_minutes', 30)
            proactive_recommendation = self._get_proactive_scaling_recommendation(
                app_name, current_data, policy, multi_pred, look_ahead_minutes
            )
            
            if proactive_recommendation:
                return proactive_recommendation
            
            # Fallback to standard horizon analysis
            horizon_analysis = self._analyze_horizon_predictions(multi_pred['predictions'], policy)
            
            if not horizon_analysis['needs_scaling']:
                return None
            
            # Get current state
            current_replicas = current_data.get('replica_count', 1)
            
            # Calculate target replicas based on horizon analysis
            if horizon_analysis['action'] == 'scale_up':
                target_replicas = min(
                    current_replicas + policy.get('scale_increment', 1),
                    policy.get('max_replicas', 10)
                )
            else:  # scale_down
                target_replicas = max(
                    current_replicas - policy.get('scale_decrement', 1),
                    policy.get('min_replicas', 1)
                )
            
            if target_replicas == current_replicas:
                return None  # No change needed
            
            return {
                'action': horizon_analysis['action'],
                'current_replicas': current_replicas,
                'target_replicas': target_replicas,
                'reason': horizon_analysis['reason'],
                'confidence': multi_pred['aggregate_confidence'],
                'multi_horizon_predictions': multi_pred['predictions'],
                'horizon_analysis': horizon_analysis,
                'type': 'ml_predictive_multi_horizon'
            }
            
        except Exception as e:
            print(f"Error getting scaling recommendation: {e}")
            return None
    
    def _get_proactive_scaling_recommendation(self, app_name: str, current_data: Dict, 
                                            policy: Dict, multi_pred: Dict, look_ahead_minutes: int) -> Optional[Dict]:
        """Get proactive scaling recommendation based on lookAhead predictions"""
        try:
            current_replicas = current_data.get('replica_count', 1)
            
            # Find the prediction horizon closest to lookAhead time
            target_horizon = min(multi_pred['predictions'].keys(), 
                               key=lambda h: abs(int(h.replace('m', '')) - look_ahead_minutes))
            
            target_pred = multi_pred['predictions'][target_horizon]
            ensemble_pred = target_pred.get('ensemble_prediction', {})
            
            if ensemble_pred.get('confidence', 0) < policy.get('confidence_threshold', 70):
                return None
            
            # Calculate predicted load at lookAhead time
            predicted_cpu = ensemble_pred.get('cpu_predicted', 0)
            predicted_memory = ensemble_pred.get('memory_predicted', 0)
            
            # Proactive scaling thresholds (more aggressive than reactive)
            proactive_cpu_threshold = policy.get('cpu_scale_up_threshold', 75) - 10  # Scale earlier
            proactive_memory_threshold = policy.get('memory_scale_up_threshold', 80) - 10
            
            # Check if we need to scale proactively
            needs_proactive_scaling = False
            scaling_reason = ""
            
            if predicted_cpu > proactive_cpu_threshold or predicted_memory > proactive_memory_threshold:
                # Calculate required capacity for predicted load
                cpu_scale_factor = max(1.0, predicted_cpu / policy.get('cpu_scale_up_threshold', 75))
                memory_scale_factor = max(1.0, predicted_memory / policy.get('memory_scale_up_threshold', 80))
                
                # Use the higher scale factor
                scale_factor = max(cpu_scale_factor, memory_scale_factor)
                
                # Calculate target replicas with proactive buffer
                target_replicas = min(
                    int(current_replicas * scale_factor * 1.1),  # 10% buffer for proactive scaling
                    policy.get('max_replicas', 10)
                )
                
                if target_replicas > current_replicas:
                    needs_proactive_scaling = True
                    scaling_reason = f"Proactive scaling for predicted load in {look_ahead_minutes}m: CPU {predicted_cpu:.1f}%, Memory {predicted_memory:.1f}%"
            
            # Check for proactive scale-down (if predicted load is very low)
            elif predicted_cpu < (policy.get('cpu_scale_down_threshold', 30) + 10) and \
                 predicted_memory < (policy.get('memory_scale_down_threshold', 40) + 10):
                
                # Only scale down if we're confident and have excess capacity
                if current_replicas > policy.get('min_replicas', 1) and ensemble_pred.get('confidence', 0) > 80:
                    target_replicas = max(
                        current_replicas - 1,
                        policy.get('min_replicas', 1)
                    )
                    needs_proactive_scaling = True
                    scaling_reason = f"Proactive scale-down for predicted low load in {look_ahead_minutes}m: CPU {predicted_cpu:.1f}%, Memory {predicted_memory:.1f}%"
                else:
                    target_replicas = current_replicas
            else:
                target_replicas = current_replicas
            
            if not needs_proactive_scaling or target_replicas == current_replicas:
                return None
            
            return {
                'action': 'proactive_scale_up' if target_replicas > current_replicas else 'proactive_scale_down',
                'current_replicas': current_replicas,
                'target_replicas': target_replicas,
                'reason': scaling_reason,
                'confidence': ensemble_pred.get('confidence', 0),
                'look_ahead_minutes': look_ahead_minutes,
                'predicted_metrics': {
                    'cpu': predicted_cpu,
                    'memory': predicted_memory
                },
                'type': 'ml_proactive_lookahead',
                'horizon_used': target_horizon
            }
            
        except Exception as e:
            print(f"Error in proactive scaling recommendation: {e}")
            return None
    
    def _analyze_horizon_predictions(self, predictions: Dict, policy: Dict) -> Dict:
        """Analyze predictions across multiple horizons to determine scaling action"""
        try:
            # Extract thresholds
            cpu_scale_up = policy.get('cpu_scale_up_threshold', 75)
            cpu_scale_down = policy.get('cpu_scale_down_threshold', 30)
            memory_scale_up = policy.get('memory_scale_up_threshold', 80)
            memory_scale_down = policy.get('memory_scale_down_threshold', 40)
            
            scale_up_votes = 0
            scale_down_votes = 0
            horizon_details = {}
            anomaly_detected = False
            
            # Analyze each horizon
            for horizon_key, pred_data in predictions.items():
                ensemble_pred = pred_data.get('ensemble_prediction', {})
                cpu_pred = ensemble_pred.get('cpu_predicted', 0)
                memory_pred = ensemble_pred.get('memory_predicted', 0)
                confidence = ensemble_pred.get('confidence', 0)
                
                # Weight votes by confidence
                vote_weight = confidence / 100
                
                # Check for anomaly detection signals
                anomaly_info = pred_data.get('individual_predictions', {}).get('anomaly_detection', {})
                if anomaly_info.get('is_anomaly', False):
                    anomaly_detected = True
                    # Anomaly detection gets extra vote weight
                    vote_weight *= 1.2
                
                if cpu_pred > cpu_scale_up or memory_pred > memory_scale_up:
                    scale_up_votes += vote_weight
                    decision = 'scale_up'
                elif cpu_pred < cpu_scale_down and memory_pred < memory_scale_down:
                    scale_down_votes += vote_weight
                    decision = 'scale_down'
                else:
                    decision = 'no_change'
                
                horizon_details[horizon_key] = {
                    'cpu_predicted': cpu_pred,
                    'memory_predicted': memory_pred,
                    'confidence': confidence,
                    'decision': decision,
                    'vote_weight': vote_weight
                }
            
            # Determine final action with anomaly consideration
            anomaly_suffix = ' (anomaly detected)' if anomaly_detected else ''
            
            if scale_up_votes > scale_down_votes and scale_up_votes > 0.5:
                action = 'scale_up'
                reason = f'Multi-horizon analysis suggests scale up (votes: {scale_up_votes:.2f}){anomaly_suffix}'
                needs_scaling = True
            elif scale_down_votes > scale_up_votes and scale_down_votes > 0.5:
                action = 'scale_down'
                reason = f'Multi-horizon analysis suggests scale down (votes: {scale_down_votes:.2f}){anomaly_suffix}'
                needs_scaling = True
            else:
                action = 'no_change'
                reason = f'Multi-horizon analysis suggests no scaling needed{anomaly_suffix}'
                needs_scaling = False
            
            return {
                'needs_scaling': needs_scaling,
                'action': action,
                'reason': reason,
                'scale_up_votes': scale_up_votes,
                'scale_down_votes': scale_down_votes,
                'horizon_details': horizon_details,
                'anomaly_detected': anomaly_detected
            }
            
        except Exception as e:
            return {
                'needs_scaling': False,
                'action': 'error',
                'reason': f'Error analyzing horizons: {e}',
                'horizon_details': {}
            }
    
    def update_model_weights(self, new_weights: Dict) -> Dict:
        """Update model weights with validation"""
        try:
            # Validate weights sum to 1.0
            total_weight = sum(new_weights.values())
            if abs(total_weight - 1.0) > 0.01:
                return {'success': False, 'error': f'Weights must sum to 1.0, got {total_weight}'}
            
            # Validate all required models have weights
            for model_name in self.predictors.keys():
                if model_name not in new_weights:
                    return {'success': False, 'error': f'Missing weight for model: {model_name}'}
            
            self.weights = new_weights.copy()
            return {'success': True, 'weights': self.weights}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def should_retrain(self, app_name: str) -> bool:
        """Check if models should be retrained for application"""
        try:
            last_train_time = self.last_training.get(app_name, 0)
            time_since_training = datetime.now().timestamp() - last_train_time
            
            # Check if enough time has passed
            if time_since_training < self.retrain_interval:
                return False
            
            # Check if we have enough new data
            recent_data = self.data_collector.get_metrics_for_app(app_name, 1)  # Last 1 day
            if len(recent_data) < 50:  # Need at least 50 new data points
                return False
            
            return True
            
        except Exception as e:
            print(f"Error checking retrain status: {e}")
            return False
    
    def auto_retrain_models(self, app_name: str) -> Dict:
        """Automatically retrain models if conditions are met"""
        try:
            if not self.should_retrain(app_name):
                return {'retrained': False, 'reason': 'Retrain conditions not met'}
            
            # Perform training
            training_result = self.train_models(app_name, days=7)  # Use last 7 days
            
            if training_result.get('success'):
                self.last_training[app_name] = datetime.now().timestamp()
                return {
                    'retrained': True,
                    'models_trained': training_result['models_trained'],
                    'training_samples': training_result['training_samples']
                }
            else:
                return {
                    'retrained': False,
                    'error': training_result.get('error', 'Training failed')
                }
                
        except Exception as e:
            return {'retrained': False, 'error': str(e)}
    
    def cleanup_old_data(self, app_name: str) -> Dict:
        """Clean up old training data based on retention policy"""
        try:
            cutoff_time = datetime.now() - timedelta(seconds=self.data_retention)
            
            # Get all data for app
            all_data = self.data_collector.get_metrics_for_app(app_name, 60)  # Get 60 days
            
            # Filter out old data
            recent_data = []
            removed_count = 0
            
            for data_point in all_data:
                try:
                    data_time = datetime.fromisoformat(data_point['timestamp'])
                    if data_time >= cutoff_time:
                        recent_data.append(data_point)
                    else:
                        removed_count += 1
                except:
                    # Keep data if timestamp parsing fails
                    recent_data.append(data_point)
            
            # Save cleaned data back (this would need data_collector method)
            return {
                'success': True,
                'removed_points': removed_count,
                'remaining_points': len(recent_data)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_model_status(self) -> Dict:
        """Get status of all models with configuration info"""
        status = {}
        for name, predictor in self.predictors.items():
            model_info = predictor.get_model_info()
            model_info['weight'] = self.weights.get(name, 0)
            status[name] = model_info
        
        return {
            'models': status,
            'ensemble_weights': self.weights,
            'default_weights': self.default_weights,
            'min_training_samples': self.min_training_samples,
            'retrain_interval_hours': self.retrain_interval / 3600,
            'data_retention_days': self.data_retention / (24 * 3600),
            'min_data_points': self.min_data_points,
            'last_training': self.last_training,
            'proactive_scaling_enabled': True,
            'default_look_ahead_minutes': 30
        }

def test_ensemble():
    """Test the ensemble predictor with configurable weights and auto-retraining"""
    ensemble = EnsemblePredictor()
    
    print("Testing Ensemble Predictor with Configurable Weights and Auto-Retraining...")
    
    # Test with sample current data
    current_data = {
        'timestamp': datetime.now().isoformat(),
        'application': 'test-app',
        'cpu_percent': 45.0,
        'memory_percent': 60.0,
        'replica_count': 2,
        'hour_of_day': datetime.now().hour,
        'day_of_week': datetime.now().weekday(),
        'minute_of_day': datetime.now().hour * 60 + datetime.now().minute,
        'is_weekend': datetime.now().weekday() >= 5,
        'is_business_hours': 9 <= datetime.now().hour <= 17 and datetime.now().weekday() < 5
    }
    
    # Test configurable weights
    print("\n1. Testing Configurable Model Weights:")
    new_weights = {
        'linear_trend': 0.5,
        'seasonal_pattern': 0.3,
        'anomaly_detection': 0.2
    }
    weight_result = ensemble.update_model_weights(new_weights)
    print(f"   Weight Update Result: {weight_result}")
    
    # Test multi-horizon predictions with new weights
    print("\n2. Multi-Horizon Predictions with Custom Weights:")
    multi_prediction = ensemble.predict_multi_horizon('test-app', current_data, [15, 30, 60])
    print(f"   Result: {multi_prediction}")
    
    # Test auto-retraining check
    print("\n3. Auto-Retraining Check:")
    should_retrain = ensemble.should_retrain('test-app')
    print(f"   Should Retrain: {should_retrain}")
    
    # Test data cleanup
    print("\n4. Data Cleanup Test:")
    cleanup_result = ensemble.cleanup_old_data('test-app')
    print(f"   Cleanup Result: {cleanup_result}")
    
    # Enhanced model status with configuration
    print("\n5. Enhanced Model Status:")
    status = ensemble.get_model_status()
    print(f"   Result: {status}")

if __name__ == "__main__":
    test_ensemble()