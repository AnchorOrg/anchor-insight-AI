#!/usr/bin/env python3
"""
Validate Hoppscotch configuration file
"""
import json

def validate_hoppscotch_config():
    try:
        with open('docs/anchor-insight-AI.hoppscotch.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("✅ JSON is valid")
        print(f"📋 Collection: {data['name']}")
        print(f"📁 Folders: {len(data['folders'])}")
        
        total_requests = 0
        for folder in data['folders']:
            requests_count = len(folder['requests'])
            total_requests += requests_count
            print(f"  📂 {folder['name']}: {requests_count} requests")
        
        print(f"🔗 Total requests: {total_requests}")
        print("🎉 Hoppscotch configuration is ready!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    validate_hoppscotch_config()
