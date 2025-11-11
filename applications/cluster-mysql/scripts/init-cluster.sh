#!/bin/bash
set -e

echo "Initializing MySQL cluster configuration..."

# Create replication user
mysql -u root -p"$MYSQL_ROOT_PASSWORD" <<-EOSQL
    CREATE USER IF NOT EXISTS '$MYSQL_REPLICATION_USER'@'%' IDENTIFIED BY '$MYSQL_REPLICATION_PASSWORD';
    GRANT REPLICATION SLAVE ON *.* TO '$MYSQL_REPLICATION_USER'@'%';
    
    CREATE USER IF NOT EXISTS 'cluster_monitor'@'%' IDENTIFIED BY 'monitor_pass';
    GRANT SELECT, PROCESS, REPLICATION CLIENT ON *.* TO 'cluster_monitor'@'%';
    
    FLUSH PRIVILEGES;
EOSQL

# Create cluster management database
mysql -u root -p"$MYSQL_ROOT_PASSWORD" <<-EOSQL
    CREATE DATABASE IF NOT EXISTS cluster_management;
    USE cluster_management;
    
    CREATE TABLE IF NOT EXISTS nodes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        node_name VARCHAR(255) NOT NULL UNIQUE,
        host VARCHAR(255) NOT NULL,
        port INT NOT NULL DEFAULT 3306,
        role ENUM('master', 'slave') NOT NULL DEFAULT 'slave',
        status ENUM('active', 'inactive', 'maintenance') NOT NULL DEFAULT 'active',
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS cluster_config (
        config_key VARCHAR(255) PRIMARY KEY,
        config_value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );
    
    INSERT IGNORE INTO cluster_config (config_key, config_value) VALUES
    ('cluster_name', 'mysql-cluster'),
    ('auto_failover', 'true'),
    ('health_check_interval', '30'),
    ('replication_lag_threshold', '10');
EOSQL

echo "MySQL cluster initialization completed."