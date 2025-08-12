#!/usr/bin/env python3
"""
Final validation of Hoppscotch configuration
"""
import requests
import json

def test_service_availability():
    """Test if the service is responding"""
    try:
        response = requests.get('http://127.0.0.1:8003/health', timeout=5)
        print(f"✅ Service responding: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
    except Exception as e:
        print(f"⚠️  Service not responding: {e}")
        print("💡 Make sure to start the service with:")
        print("   python -m uvicorn src.main_refactored:app --host 127.0.0.1 --port 8003")
        return False

def validate_config():
    """Validate the Hoppscotch configuration file"""
    try:
        with open('docs/anchor-insight-AI.hoppscotch.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("✅ Hoppscotch JSON configuration is valid")
        
        # Count requests by folder
        folders = config['folders']
        print(f"📁 Found {len(folders)} test folders:")
        
        total_requests = 0
        for folder in folders:
            count = len(folder['requests'])
            total_requests += count
            print(f"  📂 {folder['name']}: {count} requests")
        
        print(f"🔗 Total API tests: {total_requests}")
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Final validation of Anchor Insight AI testing setup")
    print("=" * 60)
    
    config_ok = validate_config()
    service_ok = test_service_availability()
    
    print("=" * 60)
    if config_ok and service_ok:
        print("🎉 Everything is ready! You can now:")
        print("1. Open Hoppscotch")
        print("2. Import docs/anchor-insight-AI.hoppscotch.json")
        print("3. Start testing all 18 API endpoints!")
    elif config_ok:
        print("✅ Config ready, but service is not running")
        print("🔧 Start the service and try again")
    else:
        print("❌ Configuration needs to be fixed")
