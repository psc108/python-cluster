#!/usr/bin/env python3
"""
Clean up JSON files after database migration
"""

import os
import shutil

def cleanup_json_files():
    """Remove JSON files that are now stored in database"""
    files_to_remove = [
        "dashboard-data/ml_scaling_policies.json",
        "dashboard-data/ml_predictions.json", 
        "dashboard-data/ml_service_status.json",
        "dashboard-data/scaling_policies.json",
        "dashboard-data/scaling_events.json",
        "dashboard-data/scaling_analytics.json",
        "dashboard-data/scheduled_policies.json",
        "dashboard-data/ml_configuration.json",
        "dashboard-data/ml_scaling_events.json"
    ]
    
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Removed: {file_path}")
    
    # Remove app directories (thousands of them)
    apps_dir = "dashboard-data/apps"
    if os.path.exists(apps_dir):
        shutil.rmtree(apps_dir)
        print(f"Removed directory: {apps_dir}")

if __name__ == "__main__":
    cleanup_json_files()