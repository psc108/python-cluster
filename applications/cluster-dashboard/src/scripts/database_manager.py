#!/usr/bin/env python3
"""
Database Manager for cluster data operations
"""

import mysql.connector
import json
from datetime import datetime
from typing import Dict, List, Optional

class DatabaseManager:
    def __init__(self):
        self.config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'cluster_user',
            'password': 'cluster_pass',
            'database': 'cluster_db'
        }
    
    def get_connection(self):
        """Get database connection"""
        return mysql.connector.connect(**self.config)
    
    # Application operations
    def save_application(self, app_data: Dict):
        """Save application to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        sql = """INSERT INTO applications (name, image, replicas, status, ports, resources) 
                 VALUES (%s, %s, %s, %s, %s, %s)
                 ON DUPLICATE KEY UPDATE 
                 image=%s, replicas=%s, status=%s, ports=%s, resources=%s, updated_at=NOW()"""
        
        ports_json = json.dumps(app_data.get('ports', []))
        resources_json = json.dumps(app_data.get('resources', {}))
        
        values = (
            app_data['name'], app_data['image'], app_data['replicas'], 
            app_data['status'], ports_json, resources_json,
            app_data['image'], app_data['replicas'], app_data['status'], 
            ports_json, resources_json
        )
        
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
        conn.close()
    
    def get_applications(self) -> List[Dict]:
        """Get all applications"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM applications")
        apps = cursor.fetchall()
        
        for app in apps:
            app['ports'] = json.loads(app['ports']) if app['ports'] else []
            app['resources'] = json.loads(app['resources']) if app['resources'] else {}
        
        cursor.close()
        conn.close()
        return apps
    
    # Scaling policy operations
    def save_scaling_policy(self, policy: Dict):
        """Save scaling policy"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        sql = """INSERT INTO scaling_policies 
                 (application, type, min_replicas, max_replicas, cpu_threshold, memory_threshold, enabled)
                 VALUES (%s, %s, %s, %s, %s, %s, %s)
                 ON DUPLICATE KEY UPDATE
                 type=%s, min_replicas=%s, max_replicas=%s, cpu_threshold=%s, memory_threshold=%s, enabled=%s"""
        
        values = (
            policy['application'], policy.get('type', 'threshold'),
            policy['min_replicas'], policy['max_replicas'],
            policy['cpu_threshold'], policy['memory_threshold'], policy['enabled'],
            policy.get('type', 'threshold'), policy['min_replicas'], policy['max_replicas'],
            policy['cpu_threshold'], policy['memory_threshold'], policy['enabled']
        )
        
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
        conn.close()
    
    def get_scaling_policies(self) -> List[Dict]:
        """Get all scaling policies"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM scaling_policies")
        policies = cursor.fetchall()
        cursor.close()
        conn.close()
        return policies
    
    # Scaling events
    def log_scaling_event(self, event: Dict):
        """Log scaling event"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        sql = """INSERT INTO scaling_events (application, action, from_replicas, to_replicas, reason)
                 VALUES (%s, %s, %s, %s, %s)"""
        
        values = (event['application'], event['action'], event['from_replicas'], 
                 event['to_replicas'], event['reason'])
        
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
        conn.close()
    
    def get_scaling_events(self, limit: int = 100) -> List[Dict]:
        """Get recent scaling events"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM scaling_events ORDER BY timestamp DESC LIMIT %s", (limit,))
        events = cursor.fetchall()
        cursor.close()
        conn.close()
        return events
    
    # ML operations
    def save_ml_policy(self, policy: Dict):
        """Save ML policy"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        sql = """INSERT INTO ml_policies 
                 (application, prediction_horizons, confidence_threshold, model_weights, enabled)
                 VALUES (%s, %s, %s, %s, %s)
                 ON DUPLICATE KEY UPDATE
                 prediction_horizons=%s, confidence_threshold=%s, model_weights=%s, enabled=%s"""
        
        horizons_json = json.dumps(policy.get('prediction_horizons', [15, 30, 60]))
        weights_json = json.dumps(policy.get('model_weights', {}))
        
        values = (
            policy['application'], horizons_json, policy['confidence_threshold'], 
            weights_json, policy['enabled'],
            horizons_json, policy['confidence_threshold'], weights_json, policy['enabled']
        )
        
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
        conn.close()
    
    def save_ml_metrics(self, metrics: List[Dict]):
        """Save ML training metrics"""
        if not metrics:
            return
            
        conn = self.get_connection()
        cursor = conn.cursor()
        
        sql = """INSERT INTO ml_metrics 
                 (application, timestamp, cpu_percent, memory_mb, replica_count, 
                  request_rate, response_time, error_rate, throughput,
                  hour_of_day, day_of_week, is_weekend, is_business_hours)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        values = []
        for metric in metrics:
            values.append((
                metric['application'], metric['timestamp'], metric['cpu_percent'],
                metric['memory_mb'], metric['replica_count'], metric['request_rate'],
                metric['response_time'], metric['error_rate'], metric['throughput'],
                metric['hour_of_day'], metric['day_of_week'], 
                metric['is_weekend'], metric['is_business_hours']
            ))
        
        cursor.executemany(sql, values)
        conn.commit()
        cursor.close()
        conn.close()
    
    def get_ml_metrics(self, app_name: str = None, days: int = 7) -> List[Dict]:
        """Get ML training metrics"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        if app_name:
            sql = """SELECT * FROM ml_metrics 
                     WHERE application = %s AND timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                     ORDER BY timestamp DESC"""
            cursor.execute(sql, (app_name, days))
        else:
            sql = """SELECT * FROM ml_metrics 
                     WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                     ORDER BY timestamp DESC"""
            cursor.execute(sql, (days,))
        
        metrics = cursor.fetchall()
        cursor.close()
        conn.close()
        return metrics
    
    def save_ml_predictions(self, predictions: List[Dict]):
        """Save ML predictions"""
        if not predictions:
            return
            
        conn = self.get_connection()
        cursor = conn.cursor()
        
        sql = """INSERT INTO ml_predictions 
                 (application, timestamp, horizon_minutes, predicted_cpu, 
                  predicted_memory, predicted_replicas, confidence, model_used)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        
        values = []
        for pred in predictions:
            values.append((
                pred['application'], pred['timestamp'], pred['horizon_minutes'],
                pred['predicted_cpu'], pred['predicted_memory'], pred['predicted_replicas'],
                pred['confidence'], pred['model_used']
            ))
        
        cursor.executemany(sql, values)
        conn.commit()
        cursor.close()
        conn.close()
    
    # Node operations
    def update_node_status(self, node_data: Dict):
        """Update cluster node status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        sql = """INSERT INTO cluster_nodes 
                 (node_id, status, is_leader, uptime_seconds, cpu_percent, memory_percent)
                 VALUES (%s, %s, %s, %s, %s, %s)
                 ON DUPLICATE KEY UPDATE
                 status=%s, is_leader=%s, last_heartbeat=NOW(), uptime_seconds=%s,
                 cpu_percent=%s, memory_percent=%s, updated_at=NOW()"""
        
        values = (
            node_data['node_id'], node_data['status'], node_data['is_leader'],
            node_data['uptime_seconds'], node_data.get('cpu_percent', 0),
            node_data.get('memory_percent', 0),
            node_data['status'], node_data['is_leader'], node_data['uptime_seconds'],
            node_data.get('cpu_percent', 0), node_data.get('memory_percent', 0)
        )
        
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
        conn.close()
    
    def get_cluster_nodes(self) -> List[Dict]:
        """Get cluster node status"""
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM cluster_nodes ORDER BY node_id")
        nodes = cursor.fetchall()
        cursor.close()
        conn.close()
        return nodes

def main():
    """Command line interface"""
    import sys
    
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'No command specified'}))
        return
    
    db = DatabaseManager()
    command = sys.argv[1]
    
    try:
        if command == 'get_applications':
            apps = db.get_applications()
            print(json.dumps(apps, default=str))
        
        elif command == 'save_application':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'No application data provided'}))
                return
            app_data = json.loads(sys.argv[2])
            db.save_application(app_data)
            print(json.dumps({'success': True}))
        
        elif command == 'get_scaling_policies':
            policies = db.get_scaling_policies()
            print(json.dumps(policies, default=str))
        
        elif command == 'save_scaling_policy':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'No policy data provided'}))
                return
            policy_data = json.loads(sys.argv[2])
            db.save_scaling_policy(policy_data)
            print(json.dumps({'success': True}))
        
        elif command == 'get_scaling_events':
            events = db.get_scaling_events()
            print(json.dumps(events, default=str))
        
        elif command == 'log_scaling_event':
            if len(sys.argv) < 3:
                print(json.dumps({'error': 'No event data provided'}))
                return
            event_data = json.loads(sys.argv[2])
            db.log_scaling_event(event_data)
            print(json.dumps({'success': True}))
        
        else:
            print(json.dumps({'error': f'Unknown command: {command}'}))
    
    except Exception as e:
        print(json.dumps({'error': str(e)}))

if __name__ == '__main__':
    main()