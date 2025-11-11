#!/usr/bin/env python3
"""
Comprehensive Cluster Test Suite

Usage:
    python comprehensive_test.py [duration_hours]
    
Arguments:
    duration_hours    - Test duration in hours (default: 8)
                       Examples: 1, 4, 8, 12, 24

Test Components:
    Integration Tests:
        - MySQL database connectivity validation
        - Database schema verification (7 tables)
        - Dashboard API endpoint testing
        - Complete system integration validation
    
    Application Lifecycle Testing:
        - Realistic workload deployment (small/medium/large)
        - Multi-type applications (web, api, worker, cache, db)
        - Comprehensive scaling policy creation
        - ML policy creation and management
        - Scheduled scaling policies
    
    Pattern-Based ML Training:
        - Business Hours Pattern (9-17h scale-up)
        - Weekend Pattern (reduced resources)
        - Traffic Spike Pattern (sudden high-load)
        - Gradual Decline Pattern (slow traffic reduction)
        - Time-based scaling with hour-specific adjustments
    
    Stress Testing:
        - 5 background threads for continuous operations
        - Workload generator (maintains 20-25 apps)
        - Pattern testing (creates ML training patterns)
        - Scaling stress (continuous scaling operations)
        - System monitoring (stats every 5 minutes)
        - Cleanup (removes old apps every 30 minutes)
    
    Intelligent Operation Timing:
        - Business Hours (9-17): High activity, frequent operations
        - Evening (18-22): Medium activity
        - Night/Early Morning: Low activity, minimal operations

Statistics Tracked:
    - Deployments, scaling actions, policy creations
    - ML policies, pattern tests, integration tests
    - Error tracking and system health monitoring
    - Real-time ML data point collection

Requirements:
    - Cluster system running (python cluster.py start)
    - Dashboard accessible at http://localhost:8080
    - MySQL database accessible on port 3306
    - Python 3.x with requests, mysql-connector-python

Examples:
    python comprehensive_test.py        # Run for 8 hours (default)
    python comprehensive_test.py 4      # Run for 4 hours
    python comprehensive_test.py 12     # Run for 12 hours
    python comprehensive_test.py 1      # Run for 1 hour (quick test)
"""

import requests
import random
import time
import json
import threading
import mysql.connector
from datetime import datetime, timedelta
import concurrent.futures
import sys

class ComprehensiveClusterTester:
    def __init__(self):
        self.dashboard_url = "http://localhost:8080"
        self.mysql_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'cluster_user',
            'password': 'cluster_pass',
            'database': 'cluster_db'
        }
        self.apps = []
        self.workload_apps = []
        self.images = [
            "nginx:latest", "httpd:latest", "redis:latest", "postgres:latest",
            "mysql:latest", "mongo:latest", "memcached:latest", "rabbitmq:latest"
        ]
        self.app_types = {
            "web": ["nginx:latest", "httpd:latest"],
            "api": ["nginx:latest", "httpd:latest"],
            "worker": ["redis:latest", "rabbitmq:latest"],
            "cache": ["redis:latest", "memcached:latest"],
            "db": ["postgres:latest", "mysql:latest", "mongo:latest"]
        }
        self.running = True
        self.stats = {
            'deployments': 0,
            'scaling_actions': 0,
            'policy_creations': 0,
            'ml_policies': 0,
            'errors': 0,
            'workload_cycles': 0,
            'pattern_tests': 0,
            'integration_tests': 0
        }
        
    def log(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}")
        
    # ==================== INTEGRATION TESTS ====================
    
    def test_mysql_connection(self):
        """Test MySQL database connectivity"""
        try:
            conn = mysql.connector.connect(**self.mysql_config)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result[0] == 1
        except Exception as e:
            self.log(f"MySQL Error: {e}")
            return False
    
    def test_database_schema(self):
        """Verify all required tables exist"""
        required_tables = [
            'applications', 'scaling_policies', 'scaling_events',
            'ml_policies', 'ml_metrics', 'ml_predictions', 'cluster_nodes'
        ]
        
        try:
            conn = mysql.connector.connect(**self.mysql_config)
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            existing_tables = [table[0] for table in cursor.fetchall()]
            cursor.close()
            conn.close()
            
            missing_tables = [t for t in required_tables if t not in existing_tables]
            if missing_tables:
                self.log(f"Missing tables: {missing_tables}")
                return False
            
            self.log(f"Found {len(existing_tables)} database tables")
            return True
        except Exception as e:
            self.log(f"Schema Error: {e}")
            return False
    
    def test_dashboard_api(self):
        """Test dashboard API endpoints"""
        endpoints = [
            "/api/cluster.php?action=status",
            "/api/cluster.php?action=applications",
            "/api/cluster.php?action=get_scaling_policies",
            "/api/cluster.php?action=get_ml_status"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.dashboard_url}{endpoint}", timeout=5)
                if response.status_code != 200:
                    self.log(f"API Error: {endpoint} returned {response.status_code}")
                    return False
            except Exception as e:
                self.log(f"Connection Error: {e}")
                return False
        
        self.log(f"Tested {len(endpoints)} API endpoints")
        return True
    
    def run_integration_tests(self):
        """Run complete integration test suite"""
        self.log("Running Integration Tests...")
        
        tests = [
            ("MySQL Connection", self.test_mysql_connection),
            ("Database Schema", self.test_database_schema),
            ("Dashboard API", self.test_dashboard_api)
        ]
        
        passed = 0
        for test_name, test_func in tests:
            try:
                result = test_func()
                status = "PASS" if result else "FAIL"
                self.log(f"  {status}: {test_name}")
                if result:
                    passed += 1
                    self.stats['integration_tests'] += 1
            except Exception as e:
                self.log(f"  ERROR: {test_name} - {e}")
        
        self.log(f"Integration Tests: {passed}/{len(tests)} passed")
        return passed == len(tests)
    
    # ==================== APPLICATION OPERATIONS ====================
    
    def deploy_workload_app(self, app_type="web", size="medium", pattern_based=False):
        """Deploy application with realistic workload configuration"""
        app_name = f"{app_type}-{random.randint(1000, 9999)}"
        image = random.choice(self.app_types.get(app_type, self.images))
        
        # Size-based configuration
        if size == "small":
            replicas = random.randint(1, 2)
            cpu = f"{random.randint(50, 200)}m"
            memory = f"{random.randint(64, 256)}Mi"
        elif size == "medium":
            replicas = random.randint(2, 4)
            cpu = f"{random.randint(200, 500)}m"
            memory = f"{random.randint(256, 512)}Mi"
        else:  # large
            replicas = random.randint(3, 6)
            cpu = f"{random.randint(500, 1000)}m"
            memory = f"{random.randint(512, 1024)}Mi"
        
        # Pattern-based deployment for ML training
        if pattern_based:
            current_hour = datetime.now().hour
            if 9 <= current_hour <= 11:  # Morning ramp-up
                replicas = min(replicas + 2, 6)
            elif 12 <= current_hour <= 14:  # Lunch peak
                replicas = min(replicas + 3, 8)
            elif 15 <= current_hour <= 17:  # Afternoon high
                replicas = min(replicas + 2, 7)
            elif 18 <= current_hour <= 20:  # Evening decline
                replicas = max(replicas - 1, 1)
            else:  # Night/early morning
                replicas = max(replicas - 2, 1)
        
        payload = {
            "name": app_name,
            "image": image,
            "replicas": replicas,
            "ports": [{"port": 8080}],
            "resources": {"cpu": cpu, "memory": memory}
        }
        
        try:
            response = requests.post(f"{self.dashboard_url}/api/cluster.php?action=deploy", 
                                   json=payload, timeout=15)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.apps.append(app_name)
                    self.workload_apps.append({
                        'name': app_name,
                        'type': app_type,
                        'size': size,
                        'replicas': replicas,
                        'deployed_at': time.time(),
                        'pattern_based': pattern_based
                    })
                    self.stats['deployments'] += 1
                    pattern_info = " (pattern-based)" if pattern_based else ""
                    self.log(f"Deployed {size} {app_type} app: {app_name} ({replicas} replicas){pattern_info}")
                    return True
                else:
                    self.stats['errors'] += 1
                    self.log(f"Deploy failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            self.stats['errors'] += 1
            self.log(f"Deploy error: {str(e)}")
        return False
    
    def create_comprehensive_scaling_policy(self, app_name):
        """Create scaling policy with realistic thresholds"""
        app_info = next((app for app in self.workload_apps if app['name'] == app_name), None)
        if not app_info:
            return False
            
        # Adjust thresholds based on app type and size
        if app_info['type'] in ['web', 'api']:
            cpu_threshold = random.randint(60, 80)
            memory_threshold = random.randint(70, 85)
            max_replicas = random.randint(6, 12)
        elif app_info['type'] == 'worker':
            cpu_threshold = random.randint(70, 90)
            memory_threshold = random.randint(75, 90)
            max_replicas = random.randint(4, 8)
        else:  # cache, db
            cpu_threshold = random.randint(50, 70)
            memory_threshold = random.randint(60, 80)
            max_replicas = random.randint(3, 6)
        
        payload = {
            "application": app_name,
            "minReplicas": max(1, app_info['replicas'] - 1),
            "maxReplicas": max_replicas,
            "cpuThreshold": cpu_threshold,
            "memoryThreshold": memory_threshold
        }
        
        try:
            response = requests.post(f"{self.dashboard_url}/api/cluster.php?action=create_scaling_policy", 
                                   json=payload, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.stats['policy_creations'] += 1
                    self.log(f"Created scaling policy for {app_name} (CPU: {cpu_threshold}%, Mem: {memory_threshold}%)")
                    return True
        except Exception as e:
            self.stats['errors'] += 1
            self.log(f"Policy creation error: {str(e)}")
        return False
    
    def create_ml_policy(self, app_name):
        """Create ML scaling policy"""
        payload = {
            "application": app_name,
            "prediction_horizon": random.choice([15, 30, 60]),
            "confidence_threshold": random.randint(70, 95),
            "min_replicas": random.randint(1, 2),
            "max_replicas": random.randint(5, 12)
        }
        
        try:
            response = requests.post(f"{self.dashboard_url}/api/cluster.php?action=create_ml_policy", 
                                   json=payload, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.stats['ml_policies'] += 1
                    self.log(f"Created ML policy for {app_name}")
                    return True
        except Exception as e:
            self.stats['errors'] += 1
            self.log(f"ML policy error: {str(e)}")
        return False
    
    def create_scheduled_policy(self, app_name):
        """Create schedule-based scaling policy"""
        schedules = [
            {"time": "08:00", "replicas": random.randint(3, 6), "name": "morning-ramp"},
            {"time": "12:00", "replicas": random.randint(4, 8), "name": "lunch-peak"},
            {"time": "18:00", "replicas": random.randint(2, 4), "name": "evening-down"},
            {"time": "22:00", "replicas": random.randint(1, 2), "name": "night-minimal"}
        ]
        
        schedule = random.choice(schedules)
        payload = {
            "application": app_name,
            "schedule_time": schedule["time"],
            "target_replicas": schedule["replicas"],
            "schedule_name": schedule["name"],
            "enabled": True
        }
        
        try:
            response = requests.post(f"{self.dashboard_url}/api/cluster.php?action=create_scheduled_policy", 
                                   json=payload, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.log(f"Created scheduled policy for {app_name} at {schedule['time']}")
                    return True
        except Exception as e:
            self.log(f"Scheduled policy error: {str(e)}")
        return False
    
    def aggressive_scaling_test(self, app_name):
        """Perform aggressive scaling to test system limits"""
        try:
            # Scale up aggressively
            for target in [3, 6, 8, 5, 2]:
                payload = {"application": app_name, "replicas": target}
                response = requests.post(f"{self.dashboard_url}/api/cluster.php?action=scale", 
                                       json=payload, timeout=15)
                if response.status_code == 200:
                    try:
                        result = response.json()
                        if result.get('success'):
                            self.stats['scaling_actions'] += 1
                            self.log(f"Aggressively scaled {app_name} to {target} replicas")
                        time.sleep(random.uniform(2, 5))  # Brief pause between scales
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            self.stats['errors'] += 1
            self.log(f"Aggressive scaling error: {str(e)}")
    
    # ==================== PATTERN-BASED TESTING ====================
    
    def create_business_hours_pattern(self):
        """Create applications that follow business hours patterns"""
        self.log("Creating business hours pattern...")
        
        # Deploy apps with business hours scaling patterns
        for i in range(3):
            app_name = f"business-app-{i+1}"
            self.deploy_workload_app("web", "medium", pattern_based=True)
            
            if self.apps:
                recent_app = self.apps[-1]
                # Create time-based scaling policies
                self.create_comprehensive_scaling_policy(recent_app)
                self.create_scheduled_policy(recent_app)
                self.create_ml_policy(recent_app)
        
        self.stats['pattern_tests'] += 1
    
    def create_weekend_pattern(self):
        """Create weekend traffic patterns"""
        if datetime.now().weekday() >= 5:  # Weekend
            self.log("Creating weekend pattern...")
            
            # Lower resource apps for weekend
            for i in range(2):
                self.deploy_workload_app("cache", "small", pattern_based=True)
                
            self.stats['pattern_tests'] += 1
    
    def create_spike_pattern(self):
        """Create sudden traffic spike pattern"""
        self.log("Creating traffic spike pattern...")
        
        if self.apps:
            # Rapidly scale up multiple apps
            for app_name in random.sample(self.apps, min(3, len(self.apps))):
                high_replicas = random.randint(6, 10)
                payload = {"application": app_name, "replicas": high_replicas}
                try:
                    response = requests.post(f"{self.dashboard_url}/api/cluster.php?action=scale", 
                                           json=payload, timeout=10)
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            self.stats['scaling_actions'] += 1
                            self.log(f"Spike scaled {app_name} to {high_replicas} replicas")
                except:
                    pass
                    
                time.sleep(1)  # Quick succession
        
        self.stats['pattern_tests'] += 1
    
    def create_gradual_decline_pattern(self):
        """Create gradual traffic decline pattern"""
        self.log("Creating gradual decline pattern...")
        
        if self.apps:
            # Gradually scale down apps
            for app_name in random.sample(self.apps, min(4, len(self.apps))):
                low_replicas = random.randint(1, 3)
                payload = {"application": app_name, "replicas": low_replicas}
                try:
                    response = requests.post(f"{self.dashboard_url}/api/cluster.php?action=scale", 
                                           json=payload, timeout=10)
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            self.stats['scaling_actions'] += 1
                            self.log(f"Decline scaled {app_name} to {low_replicas} replicas")
                except:
                    pass
                    
                time.sleep(random.uniform(3, 7))  # Gradual timing
        
        self.stats['pattern_tests'] += 1
    
    # ==================== BACKGROUND THREADS ====================
    
    def workload_generator_thread(self):
        """Background thread that generates continuous workload"""
        while self.running:
            try:
                if len(self.workload_apps) < 25:  # Maintain 20-25 apps
                    app_type = random.choice(list(self.app_types.keys()))
                    size = random.choices(['small', 'medium', 'large'], weights=[0.4, 0.5, 0.1])[0]
                    pattern_based = random.random() < 0.3  # 30% pattern-based
                    self.deploy_workload_app(app_type, size, pattern_based)
                    
                # Create policies for apps without them
                for app in self.workload_apps[-5:]:  # Focus on recent apps
                    if random.random() < 0.4:  # 40% chance
                        self.create_comprehensive_scaling_policy(app['name'])
                    if random.random() < 0.2:  # 20% chance for ML policy
                        self.create_ml_policy(app['name'])
                    if random.random() < 0.1:  # 10% chance for scheduled policy
                        self.create_scheduled_policy(app['name'])
                        
                time.sleep(random.uniform(15, 45))
                self.stats['workload_cycles'] += 1
                
            except Exception as e:
                self.stats['errors'] += 1
                self.log(f"Workload generator error: {str(e)}")
                time.sleep(10)
    
    def pattern_testing_thread(self):
        """Background thread for pattern-based testing"""
        while self.running:
            try:
                # Run different patterns based on time and randomness
                current_hour = datetime.now().hour
                
                if 9 <= current_hour <= 17 and random.random() < 0.3:
                    self.create_business_hours_pattern()
                elif datetime.now().weekday() >= 5 and random.random() < 0.2:
                    self.create_weekend_pattern()
                elif random.random() < 0.1:
                    self.create_spike_pattern()
                elif random.random() < 0.1:
                    self.create_gradual_decline_pattern()
                    
                time.sleep(random.uniform(120, 300))  # 2-5 minutes between patterns
                
            except Exception as e:
                self.stats['errors'] += 1
                time.sleep(60)
    
    def scaling_stress_thread(self):
        """Background thread for continuous scaling operations"""
        while self.running:
            try:
                if self.apps:
                    app_name = random.choice(self.apps)
                    
                    # 80% chance normal scaling, 20% aggressive
                    if random.random() < 0.8:
                        replicas = random.randint(1, 6)
                        payload = {"application": app_name, "replicas": replicas}
                        response = requests.post(f"{self.dashboard_url}/api/cluster.php?action=scale", 
                                               json=payload, timeout=10)
                        if response.status_code == 200:
                            try:
                                result = response.json()
                                if result.get('success'):
                                    self.stats['scaling_actions'] += 1
                            except json.JSONDecodeError:
                                pass
                    else:
                        self.aggressive_scaling_test(app_name)
                        
                time.sleep(random.uniform(8, 20))
                
            except Exception as e:
                self.stats['errors'] += 1
                time.sleep(10)
    
    def system_monitoring_thread(self):
        """Monitor system status and log statistics"""
        while self.running:
            try:
                # Get system status
                response = requests.get(f"{self.dashboard_url}/api/cluster.php?action=get_ml_status", timeout=5)
                if response.status_code == 200:
                    status = response.json()
                    
                    # Log comprehensive stats every 5 minutes
                    self.log(f"SYSTEM STATUS - Apps: {len(self.apps)}, "
                            f"Deployments: {self.stats['deployments']}, "
                            f"Scaling: {self.stats['scaling_actions']}, "
                            f"Policies: {self.stats['policy_creations']}, "
                            f"ML Policies: {self.stats['ml_policies']}, "
                            f"Pattern Tests: {self.stats['pattern_tests']}, "
                            f"Integration Tests: {self.stats['integration_tests']}, "
                            f"Errors: {self.stats['errors']}, "
                            f"ML Data Points: {status.get('training_data_points', 0)}")
                            
                time.sleep(300)  # Every 5 minutes
                
            except Exception as e:
                time.sleep(60)
    
    def cleanup_old_apps(self):
        """Periodically cleanup old applications"""
        while self.running:
            try:
                current_time = time.time()
                apps_to_remove = []
                
                for app in self.workload_apps:
                    # Remove apps older than 3 hours randomly
                    if (current_time - app['deployed_at']) > 10800 and random.random() < 0.2:
                        payload = {"application": app['name']}
                        response = requests.post(f"{self.dashboard_url}/api/cluster.php?action=stop", 
                                               json=payload, timeout=10)
                        if response.status_code == 200:
                            result = response.json()
                            if result.get('success'):
                                self.log(f"Cleaned up old app: {app['name']}")
                                apps_to_remove.append(app)
                                if app['name'] in self.apps:
                                    self.apps.remove(app['name'])
                
                # Remove from tracking
                for app in apps_to_remove:
                    self.workload_apps.remove(app)
                    
                time.sleep(1800)  # Every 30 minutes
                
            except Exception as e:
                self.stats['errors'] += 1
                time.sleep(300)
    
    # ==================== MAIN TEST RUNNER ====================
    
    def run_comprehensive_test(self, duration_hours=8):
        """Run comprehensive test suite for specified duration"""
        self.log(f"Starting comprehensive cluster test for {duration_hours} hours")
        
        # Run integration tests first
        if not self.run_integration_tests():
            self.log("❌ Integration tests failed - aborting comprehensive test")
            return False
        
        start_time = time.time()
        end_time = start_time + (duration_hours * 3600)
        
        # Start background threads
        threads = [
            threading.Thread(target=self.workload_generator_thread, daemon=True),
            threading.Thread(target=self.pattern_testing_thread, daemon=True),
            threading.Thread(target=self.scaling_stress_thread, daemon=True),
            threading.Thread(target=self.system_monitoring_thread, daemon=True),
            threading.Thread(target=self.cleanup_old_apps, daemon=True)
        ]
        
        for thread in threads:
            thread.start()
        
        # Initial setup - deploy some base applications
        self.log("Setting up initial applications...")
        for i in range(5):
            app_type = random.choice(list(self.app_types.keys()))
            size = random.choice(['small', 'medium', 'large'])
            self.deploy_workload_app(app_type, size, pattern_based=True)
        
        # Main test loop
        try:
            while time.time() < end_time:
                # Simulate realistic traffic patterns
                current_hour = datetime.now().hour
                
                # Business hours (9-17): High activity
                if 9 <= current_hour <= 17:
                    operation_frequency = random.uniform(2, 5)
                    deployment_chance = 0.4
                    scaling_chance = 0.6
                # Evening (18-22): Medium activity  
                elif 18 <= current_hour <= 22:
                    operation_frequency = random.uniform(5, 12)
                    deployment_chance = 0.2
                    scaling_chance = 0.4
                # Night/Early morning: Low activity
                else:
                    operation_frequency = random.uniform(10, 30)
                    deployment_chance = 0.1
                    scaling_chance = 0.2
                
                # Random operations based on time of day
                rand = random.random()
                
                if rand < deployment_chance:
                    app_type = random.choice(list(self.app_types.keys()))
                    size = random.choices(['small', 'medium', 'large'], weights=[0.3, 0.6, 0.1])[0]
                    pattern_based = random.random() < 0.4  # 40% pattern-based
                    self.deploy_workload_app(app_type, size, pattern_based)
                elif rand < deployment_chance + scaling_chance and self.apps:
                    app_name = random.choice(self.apps)
                    if random.random() < 0.8:  # Normal scaling
                        replicas = random.randint(1, 8)
                        payload = {"application": app_name, "replicas": replicas}
                        try:
                            response = requests.post(f"{self.dashboard_url}/api/cluster.php?action=scale", 
                                                   json=payload, timeout=10)
                            if response.status_code == 200:
                                try:
                                    result = response.json()
                                    if result.get('success'):
                                        self.stats['scaling_actions'] += 1
                                except json.JSONDecodeError:
                                    pass
                        except:
                            self.stats['errors'] += 1
                    else:  # Aggressive scaling
                        self.aggressive_scaling_test(app_name)
                
                # Trigger scaling evaluation periodically
                if random.random() < 0.15:  # 15% chance
                    try:
                        requests.post(f"{self.dashboard_url}/api/cluster.php?action=evaluate_scaling", timeout=5)
                    except:
                        pass
                        
                time.sleep(operation_frequency)
                
        except KeyboardInterrupt:
            self.log("Test interrupted by user")
        finally:
            self.running = False
            
        # Final statistics
        elapsed_hours = (time.time() - start_time) / 3600
        self.log(f"Comprehensive test completed after {elapsed_hours:.1f} hours")
        self.log(f"FINAL STATS:")
        self.log(f"   - Applications deployed: {self.stats['deployments']}")
        self.log(f"   - Scaling actions: {self.stats['scaling_actions']}")
        self.log(f"   - Scaling policies: {self.stats['policy_creations']}")
        self.log(f"   - ML policies: {self.stats['ml_policies']}")
        self.log(f"   - Pattern tests: {self.stats['pattern_tests']}")
        self.log(f"   - Integration tests: {self.stats['integration_tests']}")
        self.log(f"   - Workload cycles: {self.stats['workload_cycles']}")
        self.log(f"   - Total errors: {self.stats['errors']}")
        self.log(f"   - Active applications: {len(self.apps)}")
        
        return True

def main():
    """Main entry point with argument validation"""
    if len(sys.argv) > 2:
        print("Usage: python comprehensive_test.py [duration_hours]")
        print("\nArguments:")
        print("  duration_hours  - Test duration in hours (default: 8)")
        print("                   Valid range: 1-24 hours")
        print("\nExamples:")
        print("  python comprehensive_test.py     # 8 hours")
        print("  python comprehensive_test.py 4   # 4 hours")
        print("  python comprehensive_test.py 12  # 12 hours")
        sys.exit(1)
    
    try:
        duration = int(sys.argv[1]) if len(sys.argv) == 2 else 8
        if duration < 1 or duration > 24:
            print("Error: Duration must be between 1 and 24 hours")
            sys.exit(1)
    except ValueError:
        print("Error: Duration must be a valid integer")
        print("Usage: python comprehensive_test.py [duration_hours]")
        sys.exit(1)
    
    print(f"Starting comprehensive cluster test for {duration} hour{'s' if duration != 1 else ''}")
    print("Press Ctrl+C to stop the test early")
    print("=" * 60)
    
    tester = ComprehensiveClusterTester()
    success = tester.run_comprehensive_test(duration)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()