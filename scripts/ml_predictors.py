#!/usr/bin/env python3
"""
ML Predictors - Phase 4.2
Machine learning models for predictive scaling
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from abc import ABC, abstractmethod
import json
import os

# Check for ML dependencies
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import IsolationForest
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("Warning: scikit-learn not available. Install with: pip install scikit-learn pandas numpy")

class BasePredictor(ABC):
    """Base class for all ML predictors"""
    
    def __init__(self, name: str):
        self.name = name
        self.is_trained = False
        self.last_training = None
        self.model_metrics = {}
        
    @abstractmethod
    def train(self, data: pd.DataFrame) -> bool:
        """Train the model on historical data"""
        pass
    
    @abstractmethod
    def predict(self, current_data: Dict, horizon_minutes: int) -> Dict:
        """Make prediction for future horizon"""
        pass
    
    def get_model_info(self) -> Dict:
        """Get model information and metrics"""
        return {
            'name': self.name,
            'is_trained': self.is_trained,
            'last_training': self.last_training,
            'metrics': self.model_metrics
        }

class LinearTrendPredictor(BasePredictor):
    """Linear regression predictor for trend analysis"""
    
    def __init__(self):
        super().__init__("linear_trend")
        if ML_AVAILABLE:
            self.cpu_model = LinearRegression()
            self.memory_model = LinearRegression()
            self.scaler = StandardScaler()
        
    def train(self, data: pd.DataFrame) -> bool:
        """Train linear regression models"""
        if not ML_AVAILABLE:
            return False
            
        try:
            if len(data) < 50:  # Need minimum data points
                return False
            
            # Prepare features
            features = self._engineer_features(data)
            
            if len(features) == 0:
                return False
            
            # Scale features
            features_scaled = self.scaler.fit_transform(features)
            
            # Train CPU model
            cpu_targets = data['cpu_percent'].values
            self.cpu_model.fit(features_scaled, cpu_targets)
            
            # Train memory model  
            memory_targets = data['memory_percent'].values
            self.memory_model.fit(features_scaled, memory_targets)
            
            # Calculate training metrics
            cpu_pred = self.cpu_model.predict(features_scaled)
            memory_pred = self.memory_model.predict(features_scaled)
            
            self.model_metrics = {
                'cpu_mae': float(mean_absolute_error(cpu_targets, cpu_pred)),
                'memory_mae': float(mean_absolute_error(memory_targets, memory_pred)),
                'training_samples': len(data)
            }
            
            self.is_trained = True
            self.last_training = datetime.now().isoformat()
            return True
            
        except Exception as e:
            print(f"Error training linear model: {e}")
            return False
    
    def _engineer_features(self, data: pd.DataFrame) -> np.ndarray:
        """Engineer features for linear regression including new metrics"""
        try:
            # Time-based and application features
            features = []
            for _, row in data.iterrows():
                feature_row = [
                    row['hour_of_day'],
                    row['day_of_week'], 
                    row['minute_of_day'],
                    int(row['is_weekend']),
                    int(row['is_business_hours']),
                    row['replica_count'],
                    # New application-level metrics
                    row.get('request_rate', 0),
                    row.get('response_time', 0),
                    row.get('error_rate', 0),
                    row.get('throughput', 0)
                ]
                features.append(feature_row)
            
            return np.array(features)
            
        except Exception as e:
            print(f"Error engineering features: {e}")
            return np.array([])
    
    def predict(self, current_data: Dict, horizon_minutes: int) -> Dict:
        """Predict CPU and memory for future horizon"""
        if not ML_AVAILABLE or not self.is_trained:
            return {'confidence': 0, 'predictions': {}}
        
        try:
            # Engineer features for prediction
            current_time = datetime.fromisoformat(current_data['timestamp'])
            future_time = current_time + timedelta(minutes=horizon_minutes)
            
            features = [[
                future_time.hour,
                future_time.weekday(),
                future_time.hour * 60 + future_time.minute,
                int(future_time.weekday() >= 5),
                int(9 <= future_time.hour <= 17 and future_time.weekday() < 5),
                current_data['replica_count'],
                current_data.get('request_rate', 0),
                current_data.get('response_time', 0),
                current_data.get('error_rate', 0),
                current_data.get('throughput', 0)
            ]]
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Make predictions
            cpu_pred = self.cpu_model.predict(features_scaled)[0]
            memory_pred = self.memory_model.predict(features_scaled)[0]
            
            # Calculate confidence based on training metrics
            confidence = self._calculate_confidence()
            
            return {
                'cpu_predicted': float(max(0, min(100, cpu_pred))),
                'memory_predicted': float(max(0, min(100, memory_pred))),
                'confidence': confidence,
                'model': self.name,
                'horizon_minutes': horizon_minutes
            }
            
        except Exception as e:
            print(f"Error in linear prediction: {e}")
            return {'confidence': 0, 'predictions': {}}
    
    def _calculate_confidence(self) -> float:
        """Calculate prediction confidence based on training metrics"""
        if not self.model_metrics:
            return 0.0
        
        # Lower MAE = higher confidence
        cpu_mae = self.model_metrics.get('cpu_mae', 100)
        memory_mae = self.model_metrics.get('memory_mae', 100)
        
        # Convert MAE to confidence (0-100)
        avg_mae = (cpu_mae + memory_mae) / 2
        confidence = max(0, min(100, 100 - avg_mae))
        
        return float(confidence)

class AnomalyDetectionPredictor(BasePredictor):
    """Anomaly detection predictor using IsolationForest"""
    
    def __init__(self):
        super().__init__("anomaly_detection")
        if ML_AVAILABLE:
            self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
            self.scaler = StandardScaler()
        self.normal_patterns = {}
        self.anomaly_threshold = -0.5
        
    def train(self, data: pd.DataFrame) -> bool:
        """Train anomaly detection model"""
        if not ML_AVAILABLE:
            return False
            
        try:
            if len(data) < 100:  # Need minimum data
                return False
            
            # Prepare features for anomaly detection
            features = self._prepare_anomaly_features(data)
            
            if len(features) == 0:
                return False
            
            # Scale features
            features_scaled = self.scaler.fit_transform(features)
            
            # Train isolation forest
            self.isolation_forest.fit(features_scaled)
            
            # Calculate normal patterns for prediction
            self.normal_patterns = {
                'cpu_mean': float(data['cpu_percent'].mean()),
                'cpu_std': float(data['cpu_percent'].std()),
                'memory_mean': float(data['memory_percent'].mean()),
                'memory_std': float(data['memory_percent'].std()),
                'replica_mean': float(data['replica_count'].mean())
            }
            
            # Test model performance
            anomaly_scores = self.isolation_forest.decision_function(features_scaled)
            outliers = len(anomaly_scores[anomaly_scores < self.anomaly_threshold])
            
            self.model_metrics = {
                'training_samples': len(data),
                'outliers_detected': outliers,
                'outlier_percentage': float(outliers / len(data) * 100),
                'anomaly_threshold': self.anomaly_threshold
            }
            
            self.is_trained = True
            self.last_training = datetime.now().isoformat()
            return True
            
        except Exception as e:
            print(f"Error training anomaly detection model: {e}")
            return False
    
    def _prepare_anomaly_features(self, data: pd.DataFrame) -> np.ndarray:
        """Prepare features for anomaly detection including application metrics"""
        try:
            features = []
            for _, row in data.iterrows():
                feature_row = [
                    row['cpu_percent'],
                    row['memory_percent'],
                    row['replica_count'],
                    row['hour_of_day'],
                    row['day_of_week'],
                    int(row['is_weekend']),
                    int(row['is_business_hours']),
                    # Include application-level metrics for anomaly detection
                    row.get('request_rate', 0),
                    row.get('response_time', 0),
                    row.get('error_rate', 0)
                ]
                features.append(feature_row)
            
            return np.array(features)
            
        except Exception as e:
            print(f"Error preparing anomaly features: {e}")
            return np.array([])
    
    def predict(self, current_data: Dict, horizon_minutes: int) -> Dict:
        """Predict anomalies and suggest scaling based on deviation from normal"""
        if not ML_AVAILABLE or not self.is_trained:
            return {'confidence': 0, 'predictions': {}}
        
        try:
            # Prepare current features
            current_time = datetime.fromisoformat(current_data['timestamp'])
            features = [[
                current_data['cpu_percent'],
                current_data['memory_percent'],
                current_data['replica_count'],
                current_time.hour,
                current_time.weekday(),
                int(current_time.weekday() >= 5),
                int(9 <= current_time.hour <= 17 and current_time.weekday() < 5),
                current_data.get('request_rate', 0),
                current_data.get('response_time', 0),
                current_data.get('error_rate', 0)
            ]]
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Get anomaly score
            anomaly_score = self.isolation_forest.decision_function(features_scaled)[0]
            is_anomaly = anomaly_score < self.anomaly_threshold
            
            # Predict future values based on anomaly detection
            if is_anomaly:
                # If current state is anomalous, predict return to normal
                cpu_pred = self.normal_patterns['cpu_mean']
                memory_pred = self.normal_patterns['memory_mean']
                confidence = min(100, abs(anomaly_score) * 100)
            else:
                # If normal, predict slight increase based on trend
                cpu_current = current_data['cpu_percent']
                memory_current = current_data['memory_percent']
                
                # Small trend adjustment based on horizon
                trend_factor = 1 + (horizon_minutes / 1000)  # Small increase over time
                cpu_pred = cpu_current * trend_factor
                memory_pred = memory_current * trend_factor
                confidence = max(20, 100 - abs(anomaly_score) * 50)
            
            return {
                'cpu_predicted': float(max(0, min(100, cpu_pred))),
                'memory_predicted': float(max(0, min(100, memory_pred))),
                'confidence': float(confidence),
                'model': self.name,
                'horizon_minutes': horizon_minutes,
                'anomaly_score': float(anomaly_score),
                'is_anomaly': bool(is_anomaly)
            }
            
        except Exception as e:
            print(f"Error in anomaly prediction: {e}")
            return {'confidence': 0, 'predictions': {}}

class SeasonalPredictor(BasePredictor):
    """Seasonal pattern predictor based on historical averages"""
    
    def __init__(self):
        super().__init__("seasonal_pattern")
        self.hourly_patterns = {}
        self.daily_patterns = {}
        
    def train(self, data: pd.DataFrame) -> bool:
        """Learn seasonal patterns from historical data"""
        try:
            if len(data) < 100:  # Need minimum data
                return False
            
            # Calculate hourly patterns including application metrics
            hourly_stats = data.groupby('hour_of_day').agg({
                'cpu_percent': ['mean', 'std', 'count'],
                'memory_percent': ['mean', 'std', 'count'],
                'request_rate': ['mean', 'std', 'count'],
                'response_time': ['mean', 'std', 'count']
            })
            
            # Calculate daily patterns including application metrics
            daily_stats = data.groupby('day_of_week').agg({
                'cpu_percent': ['mean', 'std', 'count'],
                'memory_percent': ['mean', 'std', 'count'],
                'request_rate': ['mean', 'std', 'count'],
                'response_time': ['mean', 'std', 'count']
            })
            
            # Store patterns
            self.hourly_patterns = {}
            for hour in range(24):
                if hour in hourly_stats.index:
                    self.hourly_patterns[hour] = {
                        'cpu_mean': float(hourly_stats.loc[hour, ('cpu_percent', 'mean')]),
                        'cpu_std': float(hourly_stats.loc[hour, ('cpu_percent', 'std')]),
                        'memory_mean': float(hourly_stats.loc[hour, ('memory_percent', 'mean')]),
                        'memory_std': float(hourly_stats.loc[hour, ('memory_percent', 'std')]),
                        'request_rate_mean': float(hourly_stats.loc[hour, ('request_rate', 'mean')]),
                        'response_time_mean': float(hourly_stats.loc[hour, ('response_time', 'mean')]),
                        'count': int(hourly_stats.loc[hour, ('cpu_percent', 'count')])
                    }
            
            self.daily_patterns = {}
            for day in range(7):
                if day in daily_stats.index:
                    self.daily_patterns[day] = {
                        'cpu_mean': float(daily_stats.loc[day, ('cpu_percent', 'mean')]),
                        'cpu_std': float(daily_stats.loc[day, ('cpu_percent', 'std')]),
                        'memory_mean': float(daily_stats.loc[day, ('memory_percent', 'mean')]),
                        'memory_std': float(daily_stats.loc[day, ('memory_percent', 'std')]),
                        'request_rate_mean': float(daily_stats.loc[day, ('request_rate', 'mean')]),
                        'response_time_mean': float(daily_stats.loc[day, ('response_time', 'mean')]),
                        'count': int(daily_stats.loc[day, ('cpu_percent', 'count')])
                    }
            
            self.model_metrics = {
                'hourly_patterns': len(self.hourly_patterns),
                'daily_patterns': len(self.daily_patterns),
                'training_samples': len(data)
            }
            
            self.is_trained = True
            self.last_training = datetime.now().isoformat()
            return True
            
        except Exception as e:
            print(f"Error training seasonal model: {e}")
            return False
    
    def predict(self, current_data: Dict, horizon_minutes: int) -> Dict:
        """Predict based on seasonal patterns"""
        if not self.is_trained:
            return {'confidence': 0, 'predictions': {}}
        
        try:
            # Calculate target time
            current_time = datetime.fromisoformat(current_data['timestamp'])
            target_time = current_time + timedelta(minutes=horizon_minutes)
            
            # Get patterns
            hour_pattern = self.hourly_patterns.get(target_time.hour, {})
            day_pattern = self.daily_patterns.get(target_time.weekday(), {})
            
            if not hour_pattern or not day_pattern:
                return {'confidence': 0, 'predictions': {}}
            
            # Combine patterns (weighted by sample count)
            hour_weight = min(1.0, hour_pattern.get('count', 0) / 50)
            day_weight = min(1.0, day_pattern.get('count', 0) / 50)
            total_weight = hour_weight + day_weight
            
            if total_weight == 0:
                return {'confidence': 0, 'predictions': {}}
            
            # Weighted average
            cpu_pred = (hour_pattern['cpu_mean'] * hour_weight + 
                       day_pattern['cpu_mean'] * day_weight) / total_weight
            
            memory_pred = (hour_pattern['memory_mean'] * hour_weight + 
                          day_pattern['memory_mean'] * day_weight) / total_weight
            
            # Calculate confidence based on pattern consistency
            confidence = min(100, total_weight * 50)
            
            return {
                'cpu_predicted': float(max(0, min(100, cpu_pred))),
                'memory_predicted': float(max(0, min(100, memory_pred))),
                'confidence': float(confidence),
                'model': self.name,
                'horizon_minutes': horizon_minutes
            }
            
        except Exception as e:
            print(f"Error in seasonal prediction: {e}")
            return {'confidence': 0, 'predictions': {}}

def test_predictors():
    """Test the predictors with sample data"""
    if not ML_AVAILABLE:
        print("ML libraries not available for testing")
        return
    
    # Create sample data with some anomalies
    sample_data = []
    base_time = datetime.now() - timedelta(days=7)
    
    for i in range(1000):  # 1000 sample points
        timestamp = base_time + timedelta(minutes=i*10)
        
        # Simulate daily pattern
        hour_factor = 1 + 0.5 * np.sin(2 * np.pi * timestamp.hour / 24)
        
        # Add occasional anomalies (spikes)
        anomaly_factor = 1.0
        if np.random.random() < 0.05:  # 5% anomalies
            anomaly_factor = 2.0 + np.random.random()
        
        sample_data.append({
            'timestamp': timestamp.isoformat(),
            'application': 'test-app',
            'cpu_percent': max(0, min(100, (30 + 20 * hour_factor + np.random.normal(0, 5)) * anomaly_factor)),
            'memory_percent': max(0, min(100, (40 + 15 * hour_factor + np.random.normal(0, 3)) * anomaly_factor)),
            'replica_count': 2,
            'hour_of_day': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'minute_of_day': timestamp.hour * 60 + timestamp.minute,
            'is_weekend': timestamp.weekday() >= 5,
            'is_business_hours': 9 <= timestamp.hour <= 17 and timestamp.weekday() < 5
        })
    
    df = pd.DataFrame(sample_data)
    
    # Test Linear Predictor
    print("Testing Linear Trend Predictor...")
    linear_pred = LinearTrendPredictor()
    if linear_pred.train(df):
        current_data = sample_data[-1]
        prediction = linear_pred.predict(current_data, 30)
        print(f"Linear prediction: {prediction}")
    
    # Test Seasonal Predictor
    print("Testing Seasonal Predictor...")
    seasonal_pred = SeasonalPredictor()
    if seasonal_pred.train(df):
        current_data = sample_data[-1]
        prediction = seasonal_pred.predict(current_data, 30)
        print(f"Seasonal prediction: {prediction}")
    
    # Test Anomaly Detection Predictor
    print("Testing Anomaly Detection Predictor...")
    anomaly_pred = AnomalyDetectionPredictor()
    if anomaly_pred.train(df):
        current_data = sample_data[-1]
        prediction = anomaly_pred.predict(current_data, 30)
        print(f"Anomaly prediction: {prediction}")

if __name__ == "__main__":
    test_predictors()