#!/usr/bin/env python3
"""
Test cost savings breakdown functionality
"""

import requests

def test_cost_savings():
    base_url = "http://localhost:8080"
    api_url = f"{base_url}/api/cluster.php"
    
    print("Testing cost savings breakdown...")
    
    # Test cost savings breakdown API
    try:
        response = requests.get(f"{api_url}?action=cost_savings_breakdown")
        if response.status_code == 200:
            data = response.json()
            print(f"[PASS] Cost breakdown API working")
            print(f"  Scale down events: {data.get('scale_down_events', 0)}")
            print(f"  Scale down savings: ${data.get('scale_down_savings', 0)}")
            print(f"  Manual prevention count: {data.get('manual_prevention_count', 0)}")
            print(f"  Manual prevention savings: ${data.get('manual_prevention_savings', 0)}")
            return True
        else:
            print(f"[FAIL] Cost breakdown API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Cost breakdown API error: {e}")
        return False

if __name__ == "__main__":
    success = test_cost_savings()
    print("Cost savings feature ready!" if success else "Issues found")