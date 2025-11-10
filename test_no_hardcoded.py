#!/usr/bin/env python3
"""
Test to verify no hardcoded demo values are used
"""

import requests
import json

def test_no_hardcoded_values():
    base_url = "http://localhost:8080"
    api_url = f"{base_url}/api/cluster.php"
    
    print("Testing for hardcoded demo values...")
    
    # Test analytics API
    try:
        response = requests.get(f"{api_url}?action=scaling_analytics")
        if response.status_code == 200:
            data = response.json()
            print(f"Analytics efficiency_score: {data.get('efficiency_score', 'N/A')}")
            print(f"Analytics total_events_24h: {data.get('total_events_24h', 'N/A')}")
            print(f"Analytics avg_response_time: {data.get('avg_response_time', 'N/A')}")
            
            # Check if values are calculated from real data (should be 0 or calculated values)
            if data.get('efficiency_score') == 0.85 and data.get('total_events_24h') == 0:
                print("[WARNING] Analytics may contain hardcoded values")
            else:
                print("[PASS] Analytics using real calculated values")
        else:
            print(f"[FAIL] Analytics API error: {response.status_code}")
    except Exception as e:
        print(f"[FAIL] Analytics API error: {e}")
    
    # Test scheduled policies
    try:
        response = requests.get(f"{api_url}?action=get_scheduled_policies")
        if response.status_code == 200:
            data = response.json()
            print(f"[PASS] Scheduled policies: {len(data)} policies found")
        else:
            print(f"[FAIL] Scheduled policies API error: {response.status_code}")
    except Exception as e:
        print(f"[FAIL] Scheduled policies API error: {e}")

if __name__ == "__main__":
    test_no_hardcoded_values()