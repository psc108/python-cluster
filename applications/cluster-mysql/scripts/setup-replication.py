#!/usr/bin/env python3
import mysql.connector
import time
import sys
import os

def wait_for_mysql(host, port, user, password, max_attempts=30):
    """Wait for MySQL to be ready"""
    for attempt in range(max_attempts):
        try:
            conn = mysql.connector.connect(
                host=host, port=port, user=user, password=password
            )
            conn.close()
            return True
        except mysql.connector.Error:
            time.sleep(2)
    return False

def setup_replication():
    """Setup MySQL master-slave replication"""
    master_host = "mysql-master"
    slave_hosts = ["mysql-slave-1", "mysql-slave-2"]
    
    root_password = os.getenv("MYSQL_ROOT_PASSWORD", "cluster_root_pass")
    repl_user = os.getenv("MYSQL_REPLICATION_USER", "repl_user")
    repl_password = os.getenv("MYSQL_REPLICATION_PASSWORD", "repl_pass")
    
    print("Waiting for MySQL master to be ready...")
    if not wait_for_mysql(master_host, 3306, "root", root_password):
        print("Master MySQL not ready")
        sys.exit(1)
    
    # Get master status
    master_conn = mysql.connector.connect(
        host=master_host, port=3306, user="root", password=root_password
    )
    cursor = master_conn.cursor()
    cursor.execute("SHOW MASTER STATUS")
    master_status = cursor.fetchone()
    
    if not master_status:
        print("Could not get master status")
        sys.exit(1)
    
    log_file, log_pos = master_status[0], master_status[1]
    print(f"Master status: {log_file}:{log_pos}")
    
    # Setup slaves
    for slave_host in slave_hosts:
        print(f"Setting up replication for {slave_host}...")
        
        if not wait_for_mysql(slave_host, 3306, "root", root_password):
            print(f"Slave {slave_host} not ready")
            continue
        
        slave_conn = mysql.connector.connect(
            host=slave_host, port=3306, user="root", password=root_password
        )
        slave_cursor = slave_conn.cursor()
        
        # Stop slave if running
        slave_cursor.execute("STOP SLAVE")
        
        # Configure replication
        change_master_sql = f"""
        CHANGE MASTER TO
        MASTER_HOST='{master_host}',
        MASTER_USER='{repl_user}',
        MASTER_PASSWORD='{repl_password}',
        MASTER_LOG_FILE='{log_file}',
        MASTER_LOG_POS={log_pos}
        """
        slave_cursor.execute(change_master_sql)
        
        # Start slave
        slave_cursor.execute("START SLAVE")
        
        # Check slave status
        slave_cursor.execute("SHOW SLAVE STATUS")
        slave_status = slave_cursor.fetchone()
        
        if slave_status and slave_status[10] == "Yes" and slave_status[11] == "Yes":
            print(f"Replication setup successful for {slave_host}")
        else:
            print(f"Replication setup failed for {slave_host}")
        
        slave_conn.close()
    
    master_conn.close()
    print("Replication setup completed")

if __name__ == "__main__":
    setup_replication()