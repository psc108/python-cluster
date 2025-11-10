#!/usr/bin/env python3
"""
Test consolidated Auto-Scaling tab with Phase 3 features
"""

import requests

def test_consolidated_autoscaling():
    base_url = "http://localhost:8080"
    
    print("Testing consolidated Auto-Scaling tab...")
    
    # Test dashboard contains consolidated features
    response = requests.get(base_url)
    content = response.text.lower()
    
    tests = [
        ("scheduled-policies-table", "Scheduled policies table"),
        ("create schedule", "Create schedule button"),
        ("view analytics", "Analytics button"),
        ("autoscaling", "Auto-scaling tab")
    ]
    
    passed = 0
    for test_string, description in tests:
        if test_string in content:
            print(f"[PASS] {description}")
            passed += 1
        else:
            print(f"[FAIL] {description}")
    
    # Test APIs still work
    api_tests = [
        ("get_scheduled_policies", "Scheduled policies API"),
        ("scaling_analytics", "Analytics API")
    ]
    
    for action, description in api_tests:
        try:
            response = requests.get(f"{base_url}/api/cluster.php?action={action}")
            if response.status_code == 200:
                print(f"[PASS] {description}")
                passed += 1
            else:
                print(f"[FAIL] {description}")
        except:
            print(f"[FAIL] {description}")
    
    print(f"\nConsolidation test: {passed}/{len(tests) + len(api_tests)} passed")
    return passed == len(tests) + len(api_tests)

if __name__ == "__main__":
    success = test_consolidated_autoscaling()
    print("Consolidated Auto-Scaling tab ready!" if success else "Issues found")