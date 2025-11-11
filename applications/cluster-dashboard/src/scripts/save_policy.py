#!/usr/bin/env python3

import sys
import json
from database_manager import DatabaseManager

def main():
    if len(sys.argv) < 2:
        print(json.dumps({'success': False, 'error': 'Missing policy data'}))
        return
    
    try:
        policy_json = sys.argv[1]
        policy = json.loads(policy_json)
        
        db = DatabaseManager()
        db.save_scaling_policy(policy)
        
        print(json.dumps({'success': True, 'policy': policy}))
        
    except Exception as e:
        print(json.dumps({'success': False, 'error': str(e)}))

if __name__ == "__main__":
    main()