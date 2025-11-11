#!/usr/bin/env python3

import sys
import json
from database_manager import DatabaseManager

def main():
    if len(sys.argv) < 2:
        return
    
    try:
        event_json = sys.argv[1]
        event = json.loads(event_json)
        
        db = DatabaseManager()
        db.save_scaling_event(event)
        
    except Exception as e:
        pass  # Silently fail to not break scaling operations

if __name__ == "__main__":
    main()