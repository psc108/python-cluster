#!/usr/bin/env python3
"""
Database Schema Creation for Cluster System
Creates all required tables for MySQL database storage
"""

import mysql.connector
from database_manager import DatabaseManager

def create_all_tables():
    """Create all required database tables"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # ML Policies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ml_policies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            application VARCHAR(255) NOT NULL UNIQUE,
            enabled BOOLEAN DEFAULT TRUE,
            type VARCHAR(100) DEFAULT 'ml_predictive',
            prediction_horizons JSON,
            confidence_threshold INT DEFAULT 75,
            min_replicas INT DEFAULT 1,
            max_replicas INT DEFAULT 10,
            model_weights JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    # ML Scaling Events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ml_scaling_events (
            id INT AUTO_INCREMENT PRIMARY KEY,
            application VARCHAR(255) NOT NULL,
            action VARCHAR(50) NOT NULL,
            from_replicas INT,
            to_replicas INT,
            reason TEXT,
            confidence FLOAT DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_app_time (application, timestamp)
        )
    """)
    
    # Scheduled Policies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_policies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            application VARCHAR(255) NOT NULL,
            schedule_name VARCHAR(255) NOT NULL,
            time VARCHAR(10) NOT NULL,
            days JSON,
            target_replicas INT NOT NULL,
            enabled BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_schedule (application, schedule_name)
        )
    """)
    
    # ML Predictions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ml_predictions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            application VARCHAR(255) NOT NULL,
            horizon_minutes INT NOT NULL,
            predicted_cpu FLOAT,
            predicted_memory FLOAT,
            predicted_replicas INT,
            confidence FLOAT,
            model_used VARCHAR(100),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_app_time (application, timestamp)
        )
    """)
    
    # Application Deployments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS application_deployments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            image VARCHAR(500) NOT NULL,
            replicas INT DEFAULT 1,
            ports JSON,
            resources JSON,
            environment JSON,
            status VARCHAR(50) DEFAULT 'running',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("All database tables created successfully")

if __name__ == "__main__":
    create_all_tables()