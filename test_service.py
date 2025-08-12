#!/usr/bin/env python3
"""
Simple test script for the unified FastAPI service
"""
import requests
import time

def test_endpoints():
    base_url = "http://127.0.0.1:8002"
    
    print("Testing Anchor Insight AI Unified Service...")
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"✅ Root endpoint: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"✅ Health endpoint: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
    
    # Test API docs
    try:
        response = requests.get(f"{base_url}/docs", timeout=10)
        print(f"✅ API docs: {response.status_code}")
    except Exception as e:
        print(f"❌ API docs failed: {e}")
    
    # Test focus monitor endpoints (API v1)
    try:
        response = requests.get(f"{base_url}/api/v1/monitor/health", timeout=10)
        print(f"✅ Focus monitor health: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Focus monitor health failed: {e}")
    
    # Test focus score endpoints (API v1)
    try:
        response = requests.get(f"{base_url}/api/v1/analyze/health", timeout=10)
        print(f"✅ Focus score health: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Focus score health failed: {e}")

if __name__ == "__main__":
    print("Waiting 2 seconds for server to start...")
    time.sleep(2)
    test_endpoints()
