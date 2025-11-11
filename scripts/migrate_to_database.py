#!/usr/bin/env python3
"""
Complete migration from file storage to database storage
"""

from database_manager import DatabaseManager
from create_database_schema import create_all_tables
import json
import os

def migrate_all_data():
    """Migrate all existing JSON data to database"""
    print("Creating database schema...")
    create_all_tables()
    
    db = DatabaseManager()
    
    # Migrate scaling policies
    policies_file = "dashboard-data/scaling_policies.json"
    if os.path.exists(policies_file):
        with open(policies_file, 'r') as f:
            policies = json.load(f)
            for policy in policies:
                db.save_scaling_policy(policy)
        print(f"Migrated {len(policies)} scaling policies")
    
    # Migrate ML policies  
    ml_policies_file = "dashboard-data/ml_scaling_policies.json"
    if os.path.exists(ml_policies_file):
        with open(ml_policies_file, 'r') as f:
            policies = json.load(f)
            for policy in policies:
                db.save_ml_policy(policy)
        print(f"Migrated {len(policies)} ML policies")
    
    # Migrate scaling events
    events_file = "dashboard-data/scaling_events.json"
    if os.path.exists(events_file):
        with open(events_file, 'r') as f:
            events = json.load(f)
            for event in events:
                db.log_scaling_event(event)
        print(f"Migrated {len(events)} scaling events")
    
    print("Database migration completed successfully")

if __name__ == "__main__":
    migrate_all_data()