#!/usr/bin/env python3
"""
Advanced Auto-Scaler Service - Phase 3 Implementation
Supports schedule-based scaling, multi-metric decisions, cooldown management, and analytics
"""

import json
import time
import docker
import schedule
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedAutoScaler:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.cluster_api = "http://localhost:8001"
        self.dashboard_api = "http://localhost:8080/api/cluster.php"
        
        # Data files
        self.policies_file = "dashboard-data/scaling_policies.json"
        self.events_file = "dashboard-data/scaling_events.json"
        self.analytics_file = "dashboard-data/scaling_analytics.json"
        self.schedules_file = "dashboard-data/scheduled_policies.json"
        
        # Cooldown tracking
        self.last_scaling = {}
        self.scaling_history = {}
        
        # Initialize scheduler
        self.scheduler_thread = None
        self.running = True
        
    def start(self):
        """Start the advanced auto-scaler"""
        logger.info("Starting Advanced Auto-Scaler (Phase 3)")
        
        # Load scheduled policies
        self.load_scheduled_policies()
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self.run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        # Main evaluation loop
        while self.running:
            try:
                self.evaluate_all_policies()
                self.update_analytics()
                time.sleep(60)  # Evaluate every minute
            except KeyboardInterrupt:
                logger.info("Shutting down Advanced Auto-Scaler")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(30)
    
    def load_scheduled_policies(self):
        """Load and register scheduled scaling policies"""
        try:
            with open(self.schedules_file, 'r') as f:
                scheduled_policies = json.load(f)
                
            for policy in scheduled_policies:
                if policy.get('enabled', True):
                    for sched in policy.get('schedules', []):
                        if sched.get('enabled', True):
                            schedule.every().day.at(sched['time']).do(
                                self.execute_scheduled_scaling,
                                policy['application'],
                                sched['replicas'],
                                sched['name']
                            )
                            logger.info(f"Registered schedule: {sched['name']} for {policy['application']}")
                            
        except FileNotFoundError:
            logger.info("No scheduled policies found, creating empty file")
            self.save_json(self.schedules_file, [])
        except Exception as e:
            logger.error(f"Error loading scheduled policies: {e}")
    
    def run_scheduler(self):
        """Run the schedule checker in separate thread"""
        while self.running:
            schedule.run_pending()
            time.sleep(30)
    
    def evaluate_all_policies(self):
        """Evaluate all metric-based policies with advanced features"""
        try:
            policies_data = self.load_json(self.policies_file, {})
            
            # Handle both dictionary and list formats
            if isinstance(policies_data, dict):
                policies = list(policies_data.values())
            elif isinstance(policies_data, list):
                policies = policies_data
            else:
                logger.warning(f"Unexpected policies data format: {type(policies_data)}")
                return
            
            for policy in policies:
                if isinstance(policy, dict) and policy.get('enabled', False):
                    policy_type = policy.get('type', 'basic')
                    
                    if policy_type == 'multi-metric':
                        self.evaluate_multi_metric_policy(policy)
                    else:
                        self.evaluate_basic_policy(policy)
                        
        except Exception as e:
            logger.error(f"Error evaluating policies: {e}")
            logger.exception("Full traceback:")
    
    def evaluate_multi_metric_policy(self, policy: Dict):
        """Evaluate policy with multiple metrics and weighted decisions"""
        app_name = policy['application']
        
        # Check cooldown with advanced rules
        if self.is_in_advanced_cooldown(app_name, policy):
            return
        
        # Get metrics
        metrics = self.get_application_metrics(app_name)
        if not metrics:
            return
        
        # Calculate weighted score
        total_score = 0
        total_weight = 0
        
        for metric_config in policy.get('metrics', []):
            metric_name = metric_config['name']
            threshold = metric_config['threshold']
            weight = metric_config.get('weight', 1.0)
            
            if metric_name in metrics:
                current_value = metrics[metric_name]
                # Normalize score (0-1, where 1 means needs scaling)
                score = max(0, (current_value - threshold) / threshold)
                total_score += score * weight
                total_weight += weight
        
        if total_weight == 0:
            return
        
        # Calculate final decision score
        decision_score = total_score / total_weight
        
        # Determine scaling action
        current_replicas = self.get_current_replicas(app_name)
        target_replicas = current_replicas
        
        if decision_score > 0.2:  # Scale up threshold
            target_replicas = min(
                current_replicas + policy.get('scale_increment', 1),
                policy.get('maxReplicas', 10)
            )
        elif decision_score < -0.2:  # Scale down threshold
            target_replicas = max(
                current_replicas - policy.get('scale_decrement', 1),
                policy.get('minReplicas', 1)
            )
        
        if target_replicas != current_replicas:
            self.execute_scaling_with_analytics(app_name, target_replicas, policy, decision_score)
    
    def evaluate_basic_policy(self, policy: Dict):
        """Evaluate basic threshold-based policy with enhanced cooldown"""
        app_name = policy['application']
        
        if self.is_in_advanced_cooldown(app_name, policy):
            return
        
        metrics = self.get_application_metrics(app_name)
        if not metrics:
            return
        
        current_replicas = self.get_current_replicas(app_name)
        target_replicas = current_replicas
        
        cpu_threshold = policy.get('cpuThreshold', 70)
        memory_threshold = policy.get('memoryThreshold', 80)
        
        # Enhanced scaling logic with hysteresis
        scale_up_buffer = policy.get('scale_up_buffer', 10)
        scale_down_buffer = policy.get('scale_down_buffer', 20)
        
        cpu_usage = metrics.get('cpu', 0)
        memory_usage = metrics.get('memory', 0)
        
        # Scale up conditions
        if (cpu_usage > cpu_threshold + scale_up_buffer or 
            memory_usage > memory_threshold + scale_up_buffer):
            target_replicas = min(
                current_replicas + policy.get('scale_increment', 1),
                policy.get('maxReplicas', 10)
            )
        
        # Scale down conditions (with larger buffer to prevent oscillation)
        elif (cpu_usage < cpu_threshold - scale_down_buffer and 
              memory_usage < memory_threshold - scale_down_buffer):
            target_replicas = max(
                current_replicas - policy.get('scale_decrement', 1),
                policy.get('minReplicas', 1)
            )
        
        if target_replicas != current_replicas:
            self.execute_scaling_with_analytics(app_name, target_replicas, policy, 0)
    
    def is_in_advanced_cooldown(self, app_name: str, policy: Dict) -> bool:
        """Check advanced cooldown rules"""
        now = time.time()
        cooldown_config = policy.get('cooldown', {})
        
        # Check basic cooldown
        if app_name in self.last_scaling:
            last_time = self.last_scaling[app_name]['time']
            last_action = self.last_scaling[app_name]['action']
            
            # Different cooldowns for scale up/down
            if last_action == 'scale_up':
                cooldown = cooldown_config.get('scale_up', 300)
            else:
                cooldown = cooldown_config.get('scale_down', 600)
            
            if now - last_time < cooldown:
                return True
        
        # Check rate limiting
        rate_limit = policy.get('rate_limiting', {})
        max_per_hour = rate_limit.get('max_scale_per_hour', 10)
        
        if app_name in self.scaling_history:
            recent_events = [
                event for event in self.scaling_history[app_name]
                if now - event['time'] < 3600  # Last hour
            ]
            if len(recent_events) >= max_per_hour:
                logger.info(f"Rate limit reached for {app_name}: {len(recent_events)} events in last hour")
                return True
        
        return False
    
    def execute_scheduled_scaling(self, app_name: str, target_replicas: int, schedule_name: str):
        """Execute scheduled scaling action"""
        logger.info(f"Executing scheduled scaling: {app_name} -> {target_replicas} replicas ({schedule_name})")
        
        try:
            response = requests.post(f"{self.dashboard_api}?action=scale", json={
                'app_name': app_name,
                'replicas': target_replicas
            })
            
            if response.status_code == 200:
                # Log event
                event = {
                    'timestamp': datetime.now().isoformat(),
                    'application': app_name,
                    'action': 'scheduled_scaling',
                    'schedule_name': schedule_name,
                    'target_replicas': target_replicas,
                    'success': True
                }
                self.log_scaling_event(event)
                logger.info(f"Scheduled scaling successful: {app_name}")
            else:
                logger.error(f"Scheduled scaling failed: {response.text}")
                
        except Exception as e:
            logger.error(f"Error in scheduled scaling: {e}")
    
    def execute_scaling_with_analytics(self, app_name: str, target_replicas: int, policy: Dict, decision_score: float):
        """Execute scaling with enhanced analytics tracking"""
        try:
            current_replicas = self.get_current_replicas(app_name)
            action = 'scale_up' if target_replicas > current_replicas else 'scale_down'
            
            response = requests.post(f"{self.dashboard_api}?action=scale", json={
                'app_name': app_name,
                'replicas': target_replicas
            })
            
            if response.status_code == 200:
                # Update cooldown tracking
                self.last_scaling[app_name] = {
                    'time': time.time(),
                    'action': action
                }
                
                # Update scaling history
                if app_name not in self.scaling_history:
                    self.scaling_history[app_name] = []
                
                self.scaling_history[app_name].append({
                    'time': time.time(),
                    'action': action,
                    'from_replicas': current_replicas,
                    'to_replicas': target_replicas,
                    'decision_score': decision_score
                })
                
                # Log detailed event
                event = {
                    'timestamp': datetime.now().isoformat(),
                    'application': app_name,
                    'action': action,
                    'from_replicas': current_replicas,
                    'to_replicas': target_replicas,
                    'decision_score': decision_score,
                    'policy_type': policy.get('type', 'basic'),
                    'success': True
                }
                self.log_scaling_event(event)
                
                logger.info(f"Scaling executed: {app_name} {current_replicas} -> {target_replicas} (score: {decision_score:.2f})")
            else:
                logger.error(f"Scaling failed: {response.text}")
                
        except Exception as e:
            logger.error(f"Error executing scaling: {e}")
    
    def update_analytics(self):
        """Update scaling analytics data"""
        try:
            analytics = {}
            now = time.time()
            
            for app_name, history in self.scaling_history.items():
                # Filter last 24 hours
                recent_events = [
                    event for event in history
                    if now - event['time'] < 86400
                ]
                
                if recent_events:
                    scale_up_events = len([e for e in recent_events if e['action'] == 'scale_up'])
                    scale_down_events = len([e for e in recent_events if e['action'] == 'scale_down'])
                    
                    analytics[app_name] = {
                        'total_events': len(recent_events),
                        'scale_up_events': scale_up_events,
                        'scale_down_events': scale_down_events,
                        'avg_decision_score': sum(e.get('decision_score', 0) for e in recent_events) / len(recent_events),
                        'last_updated': datetime.now().isoformat()
                    }
            
            self.save_json(self.analytics_file, analytics)
            
        except Exception as e:
            logger.error(f"Error updating analytics: {e}")
    
    def get_application_metrics(self, app_name: str) -> Dict:
        """Get application metrics from cluster API"""
        try:
            response = requests.get(f"{self.dashboard_api}?action=applications")
            if response.status_code == 200:
                apps = response.json()
                for app in apps:
                    if app['name'] == app_name:
                        # Ensure numeric values
                        cpu_percent = app.get('cpu_percent', 0)
                        memory_mb = app.get('memory_mb', 0)
                        
                        # Convert memory MB to percentage (assuming 1GB = 1024MB as baseline)
                        memory_percent = (float(memory_mb) / 1024) * 100 if memory_mb else 0
                        
                        return {
                            'cpu': float(cpu_percent) if cpu_percent else 0,
                            'memory': float(memory_percent),
                            'memory_mb': float(memory_mb) if memory_mb else 0
                        }
        except Exception as e:
            logger.error(f"Error getting metrics for {app_name}: {e}")
        return {'cpu': 0, 'memory': 0, 'memory_mb': 0}
    
    def get_current_replicas(self, app_name: str) -> int:
        """Get current replica count"""
        try:
            response = requests.get(f"{self.dashboard_api}?action=applications")
            if response.status_code == 200:
                apps = response.json()
                for app in apps:
                    if app['name'] == app_name:
                        replicas_str = app.get('replicas', '0')
                        # Handle "2/3" format - take the first number (current)
                        if '/' in str(replicas_str):
                            current = str(replicas_str).split('/')[0]
                        else:
                            current = str(replicas_str)
                        return int(current)
        except Exception as e:
            logger.error(f"Error getting replica count for {app_name}: {e}")
        return 0
    
    def log_scaling_event(self, event: Dict):
        """Log scaling event to events file"""
        try:
            events = self.load_json(self.events_file, [])
            events.append(event)
            # Keep only last 1000 events
            if len(events) > 1000:
                events = events[-1000:]
            self.save_json(self.events_file, events)
        except Exception as e:
            logger.error(f"Error logging event: {e}")
    
    def load_json(self, filepath: str, default=None):
        """Load data from database instead of files"""
        try:
            from scripts.database_manager import DatabaseManager
            db = DatabaseManager()
            
            if 'scaling_policies' in filepath:
                return db.get_scaling_policies()
            elif 'scaling_events' in filepath:
                return db.get_scaling_events()
            elif 'scheduled_policies' in filepath:
                return db.get_scheduled_policies()
            else:
                return default if default is not None else {}
        except Exception:
            return default if default is not None else {}
    
    def save_json(self, filepath: str, data):
        """Save data to database instead of files"""
        try:
            from scripts.database_manager import DatabaseManager
            db = DatabaseManager()
            
            if 'scaling_policies' in filepath:
                for policy in data if isinstance(data, list) else data.values():
                    if isinstance(policy, dict):
                        db.save_scaling_policy(policy)
            elif 'scheduled_policies' in filepath:
                for policy in data:
                    db.save_scheduled_policy(policy)
        except Exception:
            pass

if __name__ == "__main__":
    scaler = AdvancedAutoScaler()
    scaler.start()