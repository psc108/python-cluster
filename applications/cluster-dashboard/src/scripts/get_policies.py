#!/usr/bin/env python3

import json
from database_manager import DatabaseManager

def main():
    try:
        db = DatabaseManager()
        policies = db.get_scaling_policies()
        
        # Convert to the format expected by the dashboard
        policies_dict = {}
        for policy in policies:
            policies_dict[policy['application']] = policy
        
        print(json.dumps(policies_dict))
        
    except Exception as e:
        print(json.dumps({}))

if __name__ == "__main__":
    main()