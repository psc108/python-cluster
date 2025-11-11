#!/usr/bin/env python3

import json
from database_manager import DatabaseManager

def main():
    try:
        db = DatabaseManager()
        events = db.get_scaling_events(limit=50)
        print(json.dumps(events))
        
    except Exception as e:
        print(json.dumps([]))

if __name__ == "__main__":
    main()