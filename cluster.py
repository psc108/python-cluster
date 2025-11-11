#!/usr/bin/env python3
"""
Unified cluster management script

Usage:
    python cluster.py start     - Start all cluster components (network, MySQL, dashboard, ML services)
    python cluster.py stop      - Stop all cluster components and containers
    python cluster.py restart   - Stop then start all components
    python cluster.py status    - Show status of all cluster components

Components managed:
    - Docker network (cluster-network)
    - MySQL database (cluster-mysql container on port 3306)
    - Cluster dashboard (cluster-dashboard container on port 8080)
    - ML data collector service
    - Advanced auto-scaler service
    - ML prediction service
    - ML auto-scaler service
    - Cluster nodes (if cluster manager exists)

Requirements:
    - Docker installed and running
    - Python 3.x with mysql-connector-python
    - Port 3306 (MySQL) and 8080 (Dashboard) available
"""

import subprocess
import sys
import os
import time
import mysql.connector

def create_network():
    """Create cluster network if it doesn't exist"""
    result = subprocess.run(["docker", "network", "create", "cluster-network"], capture_output=True)
    return result.returncode == 0 or "already exists" in result.stderr.decode()

def deploy_mysql():
    """Deploy and setup MySQL database"""
    # Stop existing MySQL if running
    subprocess.run(["docker", "stop", "cluster-mysql"], capture_output=True)
    subprocess.run(["docker", "rm", "cluster-mysql"], capture_output=True)
    
    cmd = [
        "docker", "run", "-d",
        "--name", "cluster-mysql",
        "--network", "cluster-network",
        "--restart", "unless-stopped",
        "-p", "3306:3306",
        "-e", "MYSQL_ROOT_PASSWORD=cluster_root_pass",
        "-e", "MYSQL_DATABASE=cluster_db",
        "-e", "MYSQL_USER=cluster_user",
        "-e", "MYSQL_PASSWORD=cluster_pass",
        "-v", "cluster-mysql-data:/var/lib/mysql",
        "mysql:8.0.35"
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        return False
    
    time.sleep(15)  # Wait for MySQL startup
    return setup_database()

def setup_database():
    """Create database schema"""
    try:
        conn = mysql.connector.connect(
            host='localhost', port=3306, user='cluster_user',
            password='cluster_pass', database='cluster_db'
        )
        cursor = conn.cursor()
        
        tables = [
            """CREATE TABLE IF NOT EXISTS applications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                image VARCHAR(255) NOT NULL,
                replicas INT DEFAULT 1,
                status VARCHAR(50) DEFAULT 'stopped',
                ports JSON,
                resources JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS scaling_policies (
                id INT AUTO_INCREMENT PRIMARY KEY,
                application VARCHAR(255) NOT NULL,
                type VARCHAR(50) DEFAULT 'threshold',
                min_replicas INT DEFAULT 1,
                max_replicas INT DEFAULT 10,
                cpu_threshold INT DEFAULT 70,
                memory_threshold INT DEFAULT 80,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS scaling_events (
                id INT AUTO_INCREMENT PRIMARY KEY,
                application VARCHAR(255) NOT NULL,
                action VARCHAR(50) NOT NULL,
                from_replicas INT,
                to_replicas INT,
                reason TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS ml_policies (
                id INT AUTO_INCREMENT PRIMARY KEY,
                application VARCHAR(255) NOT NULL,
                prediction_horizons JSON,
                confidence_threshold INT DEFAULT 75,
                model_weights JSON,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS ml_metrics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                application VARCHAR(255) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cpu_percent DECIMAL(5,2),
                memory_mb DECIMAL(10,2),
                replica_count INT,
                request_rate DECIMAL(10,2),
                response_time DECIMAL(10,2),
                error_rate DECIMAL(5,2),
                throughput DECIMAL(10,2),
                hour_of_day INT,
                day_of_week INT,
                is_weekend BOOLEAN,
                is_business_hours BOOLEAN,
                INDEX idx_app_timestamp (application, timestamp)
            )""",
            """CREATE TABLE IF NOT EXISTS ml_predictions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                application VARCHAR(255) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                horizon_minutes INT,
                predicted_cpu DECIMAL(5,2),
                predicted_memory DECIMAL(10,2),
                predicted_replicas INT,
                confidence DECIMAL(5,2),
                model_used VARCHAR(100)
            )""",
            """CREATE TABLE IF NOT EXISTS cluster_nodes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                node_id INT NOT NULL UNIQUE,
                status VARCHAR(50) DEFAULT 'unknown',
                is_leader BOOLEAN DEFAULT FALSE,
                last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                uptime_seconds INT DEFAULT 0,
                cpu_percent DECIMAL(5,2),
                memory_percent DECIMAL(5,2),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )"""
        ]
        
        for table_sql in tables:
            cursor.execute(table_sql)
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception:
        return False

def start_cluster():
    """Start all cluster components"""
    """Start all cluster components"""
    cluster_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("CLUSTER SYSTEM STARTUP")
    print("=" * 50)
    
    print("1. Creating cluster network...", end=" ")
    if create_network():
        print("OK")
    else:
        print("FAILED")
        return False
    
    print("2. Starting MySQL database...", end=" ")
    if deploy_mysql():
        print("OK")
    else:
        print("FAILED")
        return False
    
    print("3. Starting cluster nodes...", end=" ")
    if os.path.exists(os.path.join(cluster_dir, "docker", "scripts", "cluster_manager.py")):
        result = subprocess.run([sys.executable, "docker/scripts/cluster_manager.py", "start"], 
                              cwd=cluster_dir, capture_output=True)
        print("OK" if result.returncode == 0 else "FAILED")
    else:
        print("WARNING - Cluster manager not found")
    
    print("4. Starting dashboard...", end=" ")
    subprocess.run(["docker", "stop", "cluster-dashboard"], capture_output=True)
    subprocess.run(["docker", "rm", "cluster-dashboard"], capture_output=True)
    
    dashboard_dir = os.path.join(cluster_dir, "applications", "cluster-dashboard")
    build_result = subprocess.run(["docker", "build", "-t", "cluster-dashboard:latest", "."], 
                                cwd=dashboard_dir, capture_output=True)
    
    if build_result.returncode == 0:
        run_result = subprocess.run([
            "docker", "run", "-d", "--name", "cluster-dashboard", 
            "--network", "cluster-network", "-p", "8080:80",
            "-v", "/var/run/docker.sock:/var/run/docker.sock",
            "-v", f"{cluster_dir}/dashboard-data:/var/www/html/data",
            "cluster-dashboard:latest"
        ], capture_output=True)
        print("OK" if run_result.returncode == 0 else "FAILED")
    else:
        print("FAILED")
    
    # Start ML services
    ml_services = [
        ("5. Starting ML data collector...", "scripts/ml_data_collector.py"),
        ("6. Starting auto-scaler...", "scripts/advanced_autoscaler.py"),
        ("7. Starting ML prediction service...", "scripts/ml_prediction_service.py"),
        ("8. Starting ML auto-scaler...", "scripts/ml_autoscaler.py")
    ]
    
    for msg, script in ml_services:
        print(msg, end=" ")
        if os.path.exists(os.path.join(cluster_dir, script)):
            subprocess.Popen([sys.executable, script], cwd=cluster_dir)
            print("OK")
        else:
            print("WARNING - Not found")
    
    print("\nCLUSTER SYSTEM STARTED")
    print("=" * 50)
    print("Dashboard: http://localhost:8080")
    print("Database: MySQL on port 3306")
    return True

def stop_cluster():
    """Stop all cluster components"""
    """Stop all cluster components"""
    cluster_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("CLUSTER SYSTEM SHUTDOWN")
    print("=" * 50)
    
    # Stop containers
    containers = [
        ("1. Stopping dashboard...", "cluster-dashboard"),
        ("2. Stopping MySQL database...", "cluster-mysql")
    ]
    
    for msg, container in containers:
        print(msg, end=" ")
        result1 = subprocess.run(["docker", "stop", container], capture_output=True)
        result2 = subprocess.run(["docker", "rm", container], capture_output=True)
        print("OK" if (result1.returncode == 0 or result2.returncode == 0) else "WARNING")
    
    print("3. Stopping cluster nodes...", end=" ")
    if os.path.exists(os.path.join(cluster_dir, "docker", "scripts", "cluster_manager.py")):
        result = subprocess.run([sys.executable, "docker/scripts/cluster_manager.py", "stop"], 
                              cwd=cluster_dir, capture_output=True)
        print("OK" if result.returncode == 0 else "WARNING")
    else:
        print("WARNING - Cluster manager not found")
    
    print("4. Stopping ML services...", end=" ")
    # Kill Python processes for ML services
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/f", "/im", "python.exe"], capture_output=True)
        else:
            subprocess.run(["pkill", "-f", "ml_data_collector.py"], capture_output=True)
            subprocess.run(["pkill", "-f", "advanced_autoscaler.py"], capture_output=True)
            subprocess.run(["pkill", "-f", "ml_prediction_service.py"], capture_output=True)
            subprocess.run(["pkill", "-f", "ml_autoscaler.py"], capture_output=True)
        print("OK")
    except:
        print("WARNING")
    
    print("\nCLUSTER SYSTEM STOPPED")
    print("=" * 50)
    return True

def restart_cluster():
    """Restart all cluster components"""
    print("CLUSTER SYSTEM RESTART")
    print("=" * 50)
    stop_cluster()
    time.sleep(5)
    return start_cluster()

def show_status():
    """Show status of all cluster components"""
    print("CLUSTER SYSTEM STATUS")
    print("=" * 50)
    
    # Check Docker containers
    containers = ["cluster-dashboard", "cluster-mysql"]
    for container in containers:
        result = subprocess.run(["docker", "ps", "-q", "-f", f"name={container}"], capture_output=True)
        status = "RUNNING" if result.stdout.strip() else "STOPPED"
        print(f"{container}: {status}")
    
    # Check network
    result = subprocess.run(["docker", "network", "ls", "-q", "-f", "name=cluster-network"], capture_output=True)
    network_status = "EXISTS" if result.stdout.strip() else "NOT FOUND"
    print(f"cluster-network: {network_status}")
    
    # Check MySQL connectivity
    try:
        conn = mysql.connector.connect(
            host='localhost', port=3306, user='cluster_user',
            password='cluster_pass', database='cluster_db', connection_timeout=3
        )
        conn.close()
        print("MySQL database: ACCESSIBLE")
    except:
        print("MySQL database: NOT ACCESSIBLE")
    
    # Check dashboard
    try:
        import requests
        response = requests.get("http://localhost:8080", timeout=3)
        dashboard_status = "ACCESSIBLE" if response.status_code == 200 else "ERROR"
    except:
        dashboard_status = "NOT ACCESSIBLE"
    print(f"Dashboard (http://localhost:8080): {dashboard_status}")
    
    print("=" * 50)
    return True

def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python cluster.py [start|stop|restart|status]")
        print("\nCommands:")
        print("  start    - Start all cluster components")
        print("  stop     - Stop all cluster components")
        print("  restart  - Restart all cluster components")
        print("  status   - Show cluster component status")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "start":
        success = start_cluster()
    elif command == "stop":
        success = stop_cluster()
    elif command == "restart":
        success = restart_cluster()
    elif command == "status":
        success = show_status()
    else:
        print(f"Unknown command: {command}")
        print("Valid commands: start, stop, restart, status")
        sys.exit(1)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()