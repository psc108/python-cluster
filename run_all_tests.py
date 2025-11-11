#!/usr/bin/env python3
"""
Master Test Runner - Execute all integration tests
"""

import subprocess
import sys
import time

def run_test_suite():
    """Run complete test suite"""
    print("CLUSTER INTEGRATION TEST SUITE")
    print("=" * 60)
    print("Testing all cluster components and integrations...")
    print()
    
    tests = [
        ("Database Operations Test", "test_database_operations.py"),
        ("ML Integration Test", "test_ml_integration.py"),
        ("Full Integration Test", "test_integration.py")
    ]
    
    results = []
    
    for test_name, test_file in tests:
        print(f"Running {test_name}...")
        print("-" * 40)
        
        try:
            result = subprocess.run([sys.executable, test_file], 
                                  capture_output=False, 
                                  text=True, 
                                  timeout=60)
            
            success = result.returncode == 0
            results.append((test_name, success))
            
            if success:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_name} TIMED OUT")
            results.append((test_name, False))
        except Exception as e:
            print(f"💥 {test_name} ERROR: {e}")
            results.append((test_name, False))
        
        print()
        time.sleep(2)
    
    # Print final summary
    print("=" * 60)
    print("FINAL TEST RESULTS")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    total = len(results)
    print(f"\nOVERALL: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Cluster system is fully integrated and working")
        print("✅ MySQL database integration successful")
        print("✅ ML services integrated with database")
        print("✅ Dashboard API working with database")
        print("✅ End-to-end workflows functional")
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed")
        print("❌ System integration needs attention")
    
    return passed == total

if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1)