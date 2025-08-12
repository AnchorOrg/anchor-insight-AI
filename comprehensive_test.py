#!/usr/bin/env python3
"""
Final comprehensive test for anchor-insight-AI unified service
Tests all major components and endpoints
"""
import requests
import time
import sys

def test_comprehensive():
    base_url = "http://127.0.0.1:8003"
    
    print("🚀 Starting comprehensive test of Anchor Insight AI Unified Service")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Root endpoint
    tests_total += 1
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Test 1 PASSED: Root endpoint (200)")
            print(f"   Message: {data.get('message', 'N/A')}")
            print(f"   Version: {data.get('version', 'N/A')}")
            tests_passed += 1
        else:
            print(f"❌ Test 1 FAILED: Root endpoint ({response.status_code})")
    except Exception as e:
        print(f"❌ Test 1 ERROR: {e}")
    
    # Test 2: Health endpoint
    tests_total += 1
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Test 2 PASSED: Health endpoint (200)")
            print(f"   Status: {data.get('status', 'N/A')}")
            tests_passed += 1
        else:
            print(f"❌ Test 2 FAILED: Health endpoint ({response.status_code})")
    except Exception as e:
        print(f"❌ Test 2 ERROR: {e}")
    
    # Test 3: API Documentation
    tests_total += 1
    try:
        response = requests.get(f"{base_url}/docs", timeout=10)
        if response.status_code == 200:
            print(f"✅ Test 3 PASSED: API docs endpoint (200)")
            tests_passed += 1
        else:
            print(f"❌ Test 3 FAILED: API docs endpoint ({response.status_code})")
    except Exception as e:
        print(f"❌ Test 3 ERROR: {e}")
    
    # Test 4: Focus Monitor Health (API v1)
    tests_total += 1
    try:
        response = requests.get(f"{base_url}/api/v1/monitor/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Test 4 PASSED: Focus monitor health (200)")
            print(f"   API Version: {data.get('api_version', 'N/A')}")
            tests_passed += 1
        else:
            print(f"❌ Test 4 FAILED: Focus monitor health ({response.status_code})")
    except Exception as e:
        print(f"❌ Test 4 ERROR: {e}")
    
    # Test 5: Focus Score Health (API v1)
    tests_total += 1
    try:
        response = requests.get(f"{base_url}/api/v1/analyze/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Test 5 PASSED: Focus score health (200)")
            print(f"   API Version: {data.get('api_version', 'N/A')}")
            tests_passed += 1
        else:
            print(f"❌ Test 5 FAILED: Focus score health ({response.status_code})")
    except Exception as e:
        print(f"❌ Test 5 ERROR: {e}")
    
    # Summary
    print("=" * 60)
    print(f"📊 TEST SUMMARY:")
    print(f"   Tests Passed: {tests_passed}/{tests_total}")
    print(f"   Success Rate: {(tests_passed/tests_total)*100:.1f}%")
    
    if tests_passed == tests_total:
        print("🎉 ALL TESTS PASSED! The unified service is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the service.")
        return False

if __name__ == "__main__":
    print("Waiting 3 seconds for server to be ready...")
    time.sleep(3)
    
    success = test_comprehensive()
    sys.exit(0 if success else 1)
