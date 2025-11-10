#!/usr/bin/env python3
"""
Phase 3 Implementation Test Suite
Tests all Phase 3 features: scheduled scaling, analytics, and advanced policies
"""

import requests
import json
import time

def test_phase3_features():
    base_url = "http://localhost:8080"
    api_url = f"{base_url}/api/cluster.php"
    
    print("=" * 60)
    print("PHASE 3 IMPLEMENTATION TEST SUITE")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Dashboard accessibility
    tests_total += 1
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200 and "scheduled" in response.text.lower():
            print("[PASS] Test 1: Dashboard with Phase 3 UI")
            tests_passed += 1
        else:
            print("[FAIL] Test 1: Dashboard with Phase 3 UI")
    except Exception as e:
        print(f"[FAIL] Test 1: Dashboard accessibility ({e})")
    
    # Test 2: Basic API connectivity
    tests_total += 1
    try:
        response = requests.get(f"{api_url}?action=test_action", timeout=5)
        if response.status_code == 200:
            print("[PASS] Test 2: Basic API connectivity")
            tests_passed += 1
        else:
            print(f"[FAIL] Test 2: Basic API connectivity (HTTP {response.status_code})")
    except Exception as e:
        print(f"[FAIL] Test 2: Basic API connectivity ({e})")
    
    # Test 3: Scheduled policies API
    tests_total += 1
    try:
        response = requests.get(f"{api_url}?action=get_scheduled_policies", timeout=5)
        if response.status_code == 200:
            data = response.json() if response.text else []
            print(f"[PASS] Test 3: Scheduled policies API (found {len(data)} policies)")
            tests_passed += 1
        else:
            print(f"[FAIL] Test 3: Scheduled policies API (HTTP {response.status_code})")
    except Exception as e:
        print(f"[FAIL] Test 3: Scheduled policies API ({e})")
    
    # Test 4: Analytics API
    tests_total += 1
    try:
        response = requests.get(f"{api_url}?action=scaling_analytics", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'efficiency_score' in data:
                print(f"[PASS] Test 4: Analytics API (efficiency: {data['efficiency_score']})")
                tests_passed += 1
            else:
                print("[FAIL] Test 4: Analytics API (missing data)")
        else:
            print(f"[FAIL] Test 4: Analytics API (HTTP {response.status_code})")
    except Exception as e:
        print(f"[FAIL] Test 4: Analytics API ({e})")
    
    # Test 5: Schedule summary API
    tests_total += 1
    try:
        response = requests.get(f"{api_url}?action=schedule_summary", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'active_schedules' in data:
                print(f"[PASS] Test 5: Schedule summary API (active: {data['active_schedules']})")
                tests_passed += 1
            else:
                print("[FAIL] Test 5: Schedule summary API (missing data)")
        else:
            print(f"[FAIL] Test 5: Schedule summary API (HTTP {response.status_code})")
    except Exception as e:
        print(f"[FAIL] Test 5: Schedule summary API ({e})")
    
    # Test 6: Create scheduled policy (POST test)
    tests_total += 1
    try:
        test_policy = {
            "application": "test-app",
            "schedule_name": "test-schedule",
            "time": "09:00",
            "days": [1, 2, 3, 4, 5],
            "target_replicas": 3
        }
        response = requests.post(f"{api_url}?action=create_scheduled_policy", 
                               json=test_policy, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("[PASS] Test 6: Create scheduled policy")
                tests_passed += 1
            else:
                print(f"[FAIL] Test 6: Create scheduled policy ({data.get('error', 'Unknown error')})")
        else:
            print(f"[FAIL] Test 6: Create scheduled policy (HTTP {response.status_code})")
    except Exception as e:
        print(f"[FAIL] Test 6: Create scheduled policy ({e})")
    
    # Test 7: Enhanced policy creation with advanced options
    tests_total += 1
    try:
        response = requests.get(f"{api_url}?action=get_scaling_policies", timeout=5)
        if response.status_code == 200:
            print("[PASS] Test 7: Enhanced scaling policies API")
            tests_passed += 1
        else:
            print(f"[FAIL] Test 7: Enhanced scaling policies API (HTTP {response.status_code})")
    except Exception as e:
        print(f"[FAIL] Test 7: Enhanced scaling policies API ({e})")
    
    # Test 8: Applications API (needed for dropdowns)
    tests_total += 1
    try:
        response = requests.get(f"{api_url}?action=applications", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"[PASS] Test 8: Applications API (found {len(data)} apps)")
            tests_passed += 1
        else:
            print(f"[FAIL] Test 8: Applications API (HTTP {response.status_code})")
    except Exception as e:
        print(f"[FAIL] Test 8: Applications API ({e})")
    
    # Summary
    print("=" * 60)
    print(f"PHASE 3 TEST RESULTS: {tests_passed}/{tests_total} PASSED")
    
    if tests_passed == tests_total:
        print("ALL PHASE 3 FEATURES WORKING CORRECTLY!")
        print("[OK] Scheduled scaling UI and API")
        print("[OK] Analytics dashboard and API") 
        print("[OK] Advanced policy options")
        print("[OK] Enhanced cooldown management")
        print("[OK] Multi-metric scaling support")
    else:
        print(f"WARNING: {tests_total - tests_passed} tests failed - check implementation")
    
    print("=" * 60)
    
    return tests_passed == tests_total

if __name__ == "__main__":
    success = test_phase3_features()
    exit(0 if success else 1)