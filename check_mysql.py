#!/usr/bin/env python3
"""
Check if MySQL is running and ready
"""

import subprocess
import mysql.connector
import time

def check_mysql_status():
    """Check MySQL container and connection status"""
    print("Checking MySQL status...")
    
    # Check if container is running
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=cluster-mysql", "--format", "{{.Status}}"],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            print(f"MySQL container status: {result.stdout.strip()}")
            container_running = "Up" in result.stdout
        else:
            print("MySQL container not found")
            container_running = False
            
    except Exception as e:
        print(f"Error checking container: {e}")
        container_running = False
    
    # Check database connection
    if container_running:
        print("Testing database connection...")
        for attempt in range(3):
            try:
                conn = mysql.connector.connect(
                    host='localhost',
                    port=3306,
                    user='cluster_user',
                    password='cluster_pass',
                    database='cluster_db',
                    connection_timeout=5
                )
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if result[0] == 1:
                    print("Database connection successful!")
                    return True
                    
            except Exception as e:
                print(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(5)
    
    print("MySQL is not ready")
    return False

if __name__ == "__main__":
    check_mysql_status()