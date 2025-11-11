#!/usr/bin/env python3
"""
ML Data Collector - Phase 4.1
Enhanced metrics collection with time-series features for ML training
"""

import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from scripts.database_manager import DatabaseManager

class MLDataCollector:
    def __init__(self):
        self.dashboard_api = "http://localhost:8080/api/cluster.php"
        self.db = DatabaseManager()

        
    def collect_enhanced_metrics(self) -> List[Dict]:
        """Collect metrics with ML features for all applications"""
        try:
            response = requests.get(f"{self.dashboard_api}?action=applications", timeout=15)
            if response.status_code != 200:
                return []
                
            apps = response.json()
            enhanced_metrics = []
            
            for app in apps:
                if app.get('status') == 'running':
                    metrics = self.enhance_app_metrics(app)
                    enhanced_metrics.append(metrics)
                    
            return enhanced_metrics
            
        except Exception as e:
            print(f"Error collecting metrics: {e}")
            return []
    
    def enhance_app_metrics(self, app: Dict) -> Dict:
        """Add time-based and derived features to application metrics"""
        now = datetime.now()
        
        # Parse replica count (handle "2/3" format)
        replicas_str = str(app.get('replicas', '0'))
        current_replicas = int(replicas_str.split('/')[0]) if '/' in replicas_str else int(replicas_str)
        
        # Collect application-level metrics
        app_metrics = self.collect_application_metrics(app['name'])
        
        # Enhanced metrics with ML features
        enhanced = {
            # Basic metrics
            'timestamp': now.isoformat(),
            'application': app['name'],
            'cpu_percent': float(app.get('cpu_percent', 0)),
            'memory_mb': float(app.get('memory_mb', 0)),
            'replica_count': current_replicas,
            
            # Application-level metrics (Step 4)
            'request_rate': app_metrics['request_rate'],
            'response_time': app_metrics['response_time'],
            'error_rate': app_metrics['error_rate'],
            'throughput': app_metrics['throughput'],
            
            # Time-based features
            'hour_of_day': now.hour,
            'day_of_week': now.weekday(),  # 0=Monday, 6=Sunday
            'minute_of_day': now.hour * 60 + now.minute,
            'is_weekend': now.weekday() >= 5,
            'is_business_hours': 9 <= now.hour <= 17 and now.weekday() < 5,
            
            # Derived features
            'memory_percent': self.calculate_memory_percent(app.get('memory_mb', 0)),
            'load_score': self.calculate_load_score(app.get('cpu_percent', 0), app.get('memory_mb', 0), app_metrics['request_rate'])
        }
        
        return enhanced
    
    def calculate_memory_percent(self, memory_mb: float) -> float:
        """Convert memory MB to percentage (baseline: 1GB = 100%)"""
        if memory_mb <= 0:
            return 0.0
        return min(100.0, (memory_mb / 1024) * 100)
    
    def collect_application_metrics(self, app_name: str) -> Dict:
        """Collect application-level metrics (request rate, response time)"""
        try:
            # Get container metrics for the application
            containers = self.get_app_containers(app_name)
            if not containers:
                return self.get_default_app_metrics()
            
            # Aggregate metrics from all containers
            total_requests = 0
            total_response_time = 0
            total_errors = 0
            total_throughput = 0
            
            for container in containers:
                metrics = self.get_container_metrics(container)
                total_requests += metrics.get('requests_per_sec', 0)
                total_response_time += metrics.get('avg_response_time', 0)
                total_errors += metrics.get('error_count', 0)
                total_throughput += metrics.get('throughput_mbps', 0)
            
            container_count = len(containers)
            avg_response_time = total_response_time / container_count if container_count > 0 else 0
            error_rate = (total_errors / max(total_requests, 1)) * 100 if total_requests > 0 else 0
            
            return {
                'request_rate': round(total_requests, 2),
                'response_time': round(avg_response_time, 2),
                'error_rate': round(error_rate, 2),
                'throughput': round(total_throughput, 2)
            }
            
        except Exception as e:
            print(f"Error collecting app metrics for {app_name}: {e}")
            return self.get_default_app_metrics()
    
    def get_app_containers(self, app_name: str) -> List[str]:
        """Get list of container names for an application"""
        try:
            import subprocess
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name=app-{app_name}-', '--format', '{{.Names}}'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return [name.strip() for name in result.stdout.split('\n') if name.strip()]
        except Exception as e:
            print(f"Error getting containers for {app_name}: {e}")
        return []
    
    def get_container_metrics(self, container_name: str) -> Dict:
        """Extract metrics from container (simulated for now)"""
        try:
            # In a real implementation, this would:
            # 1. Query container logs for HTTP access patterns
            # 2. Parse nginx/apache logs for request rates
            # 3. Extract response times from application metrics
            # 4. Monitor network traffic for throughput
            
            # For now, generate realistic metrics based on container activity
            import subprocess
            import random
            
            # Check if container is running
            result = subprocess.run(
                ['docker', 'inspect', container_name, '--format', '{{.State.Running}}'],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip() == 'true':
                # Generate realistic metrics based on time of day
                now = datetime.now()
                base_load = 1.0
                
                # Business hours multiplier
                if 9 <= now.hour <= 17 and now.weekday() < 5:
                    base_load *= 2.5
                elif 18 <= now.hour <= 22:
                    base_load *= 1.5
                
                # Weekend reduction
                if now.weekday() >= 5:
                    base_load *= 0.6
                
                return {
                    'requests_per_sec': random.uniform(5, 50) * base_load,
                    'avg_response_time': random.uniform(50, 300) / base_load,
                    'error_count': random.randint(0, 5),
                    'throughput_mbps': random.uniform(0.1, 2.0) * base_load
                }
            
        except Exception as e:
            print(f"Error getting metrics for {container_name}: {e}")
        
        return self.get_default_container_metrics()
    
    def get_default_app_metrics(self) -> Dict:
        """Default metrics when collection fails"""
        return {
            'request_rate': 0.0,
            'response_time': 0.0,
            'error_rate': 0.0,
            'throughput': 0.0
        }
    
    def get_default_container_metrics(self) -> Dict:
        """Default container metrics when collection fails"""
        return {
            'requests_per_sec': 0.0,
            'avg_response_time': 0.0,
            'error_count': 0,
            'throughput_mbps': 0.0
        }
    
    def calculate_load_score(self, cpu_percent: float, memory_mb: float, request_rate: float) -> float:
        """Calculate combined load score including request rate (0-100)"""
        memory_percent = self.calculate_memory_percent(memory_mb)
        # Normalize request rate (assume 100 req/s = 100%)
        request_percent = min(100.0, request_rate)
        return (cpu_percent * 0.4 + memory_percent * 0.3 + request_percent * 0.3)
    
    def store_metrics(self, metrics: List[Dict]):
        """Store metrics to database only"""
        try:
            # Save to database
            self.db.save_ml_metrics(metrics)
            print(f"Stored {len(metrics)} metrics to database")
            
        except Exception as e:
            print(f"Error storing metrics: {e}")
    
    def load_existing_metrics(self) -> List[Dict]:
        """Load existing metrics from database"""
        try:
            return self.db.get_ml_metrics(days=30)
        except Exception as e:
            print(f"Error loading existing metrics: {e}")
        return []
    
    def get_metrics_for_app(self, app_name: str, days: int = 7) -> List[Dict]:
        """Get historical metrics for specific application"""
        try:
            return self.db.get_ml_metrics_for_app(app_name, days)
        except Exception:
            return []
    
    def get_data_summary(self) -> Dict:
        """Get summary of available training data"""
        try:
            return self.db.get_ml_data_summary()
        except Exception as e:
            print(f"Error getting data summary: {e}")
            return {'total_points': 0, 'applications': [], 'date_range': None}

def main():
    """Continuous collection loop"""
    collector = MLDataCollector()
    
    print("ML Data Collector - Continuous Mode")
    print("Collecting metrics every 5 minutes...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            # Collect current metrics
            metrics = collector.collect_enhanced_metrics()
            
            if metrics:
                collector.store_metrics(metrics)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Collected {len(metrics)} metrics")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] No applications running")
            
            # Wait 5 minutes
            time.sleep(300)
            
    except KeyboardInterrupt:
        print("\nML Data Collector stopped")
    except Exception as e:
        print(f"Error in collection loop: {e}")
        time.sleep(60)  # Wait before retrying

def collect_once():
    """Single collection for testing"""
    collector = MLDataCollector()
    
    print("ML Data Collector - Single Collection")
    print("Collecting enhanced metrics...")
    
    # Collect current metrics
    metrics = collector.collect_enhanced_metrics()
    
    if metrics:
        collector.store_metrics(metrics)
        
        # Show summary
        summary = collector.get_data_summary()
        print(f"Data Summary:")
        print(f"  Total data points: {summary['total_points']}")
        print(f"  Applications: {list(summary['applications'].keys())}")
        print(f"  Ready for ML training: {summary['ready_for_ml']}")
        
        if summary['date_range']:
            print(f"  Date range: {summary['date_range']['days']} days")
    else:
        print("No metrics collected")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "once":
        collect_once()
    else:
        main()