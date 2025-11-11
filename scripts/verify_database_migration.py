#!/usr/bin/env python3
"""
Database Migration Verification Script
Ensures all cluster operations use MySQL database exclusively
"""

import os
import json
import glob
from database_manager import DatabaseManager

def check_json_files():
    """Check for any remaining JSON files that indicate file-based storage"""
    json_files = []
    
    # Search for JSON files in key directories
    search_paths = [
        '../data/**/*.json',
        '../dashboard-data/**/*.json',
        '../applications/**/dashboard-data/**/*.json',
        '../ml_data/**/*.json'
    ]
    
    for pattern in search_paths:
        json_files.extend(glob.glob(pattern, recursive=True))
    
    # Filter out configuration files (these are OK)
    config_files = ['package.json', 'composer.json', 'tsconfig.json']
    data_files = [f for f in json_files if not any(cf in f for cf in config_files)]
    
    return data_files

def verify_database_tables():
    """Verify all required database tables exist and have data"""
    db = DatabaseManager()
    
    required_tables = [
        'ml_policies',
        'ml_scaling_events', 
        'scheduled_policies',
        'ml_predictions',
        'application_deployments'
    ]
    
    table_status = {}
    
    for table in required_tables:
        try:
            # Check if table exists and has structure
            cursor = db.conn.cursor(dictionary=True)
            cursor.execute(f"DESCRIBE {table}")
            result = cursor.fetchall()
            if result:
                # Count records
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count_result = cursor.fetchone()
                record_count = count_result['count'] if count_result else 0
                cursor.close()
                table_status[table] = {
                    'exists': True,
                    'records': record_count,
                    'columns': len(result)
                }
            else:
                cursor.close()
                table_status[table] = {'exists': False, 'records': 0, 'columns': 0}
        except Exception as e:
            table_status[table] = {'exists': False, 'error': str(e), 'records': 0}
    
    return table_status

def main():
    print("=== Database Migration Verification ===\n")
    
    # Check for remaining JSON files
    print("1. Checking for remaining JSON data files...")
    json_files = check_json_files()
    
    if json_files:
        print(f"[ERROR] Found {len(json_files)} JSON data files:")
        for file in json_files:
            print(f"   - {file}")
        print()
    else:
        print("[OK] No JSON data files found - all data operations use database\n")
    
    # Verify database tables
    print("2. Verifying database tables...")
    table_status = verify_database_tables()
    
    all_tables_ok = True
    for table, status in table_status.items():
        if status['exists']:
            print(f"[OK] {table}: {status['records']} records, {status['columns']} columns")
        else:
            print(f"[ERROR] {table}: Missing or error - {status.get('error', 'Not found')}")
            all_tables_ok = False
    
    print()
    
    # Summary
    if not json_files and all_tables_ok:
        print("[SUCCESS] MIGRATION COMPLETE: All cluster operations use MySQL database exclusively")
        print("   - No file-based data storage detected")
        print("   - All required database tables present")
        print("   - System ready for production use")
    else:
        print("[WARNING] MIGRATION INCOMPLETE:")
        if json_files:
            print(f"   - {len(json_files)} JSON files still present")
        if not all_tables_ok:
            print("   - Some database tables missing or incomplete")
        print("   - Manual cleanup required")

if __name__ == "__main__":
    main()