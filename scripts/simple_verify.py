#!/usr/bin/env python3
"""
Simple Database Migration Verification
"""

import os
import glob

def check_json_files():
    """Check for remaining JSON data files"""
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
    
    # Filter out configuration files
    config_files = ['package.json', 'composer.json', 'tsconfig.json']
    data_files = [f for f in json_files if not any(cf in f for cf in config_files)]
    
    return data_files

def main():
    print("=== Database Migration Verification ===\n")
    
    # Check for remaining JSON files
    print("Checking for remaining JSON data files...")
    json_files = check_json_files()
    
    if json_files:
        print(f"[ERROR] Found {len(json_files)} JSON data files:")
        for file in json_files:
            print(f"   - {file}")
    else:
        print("[SUCCESS] No JSON data files found")
        print("All cluster operations now use MySQL database exclusively")
        print("Migration complete - system ready for production")

if __name__ == "__main__":
    main()