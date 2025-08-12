#!/usr/bin/env python3
"""
Environment Configuration Verification Script
============================================

This script verifies that the .env configuration is properly loaded.
Run this script after setting up your .env file to ensure everything works.

Usage:
    python verify_env_config.py
"""

import os
from src.config.settings import app_settings, focus_score_settings

def main():
    print("🔍 Anchor Insight AI - Environment Configuration Verification")
    print("=" * 65)
    
    # Check if .env file exists
    env_file_exists = os.path.exists('.env')
    print(f"📄 .env file exists: {'✅ Yes' if env_file_exists else '❌ No'}")
    
    if not env_file_exists:
        print("\n⚠️  Warning: .env file not found!")
        print("   Run: cp .env.template .env")
        print("   Then edit .env with your configuration.")
        return
    
    print("\n🌍 Application Settings:")
    print(f"   Environment: {app_settings.environment}")
    print(f"   API Host: {app_settings.api_host}")
    print(f"   API Port: {app_settings.api_port}")
    print(f"   API Reload: {app_settings.api_reload}")
    print(f"   Log Level: {app_settings.log_level}")
    print(f"   Default Model Path: {app_settings.default_model_path}")
    
    print("\n🔑 Focus Score Settings:")
    print(f"   OpenAI Model: {focus_score_settings.model_id}")
    print(f"   Temperature: {focus_score_settings.temperature}")
    print(f"   Max Tokens: {focus_score_settings.max_tokens}")
    print(f"   Max File Size: {focus_score_settings.max_file_size_mb}MB")
    print(f"   Test Mode: {focus_score_settings.test_mode}")
    
    # API Key validation
    api_key = focus_score_settings.openai_api_key
    if api_key == "sk-test-key-for-testing":
        print("   OpenAI API Key: 🧪 Test key (for development)")
        if not focus_score_settings.test_mode:
            print("   ⚠️  Warning: Using test API key without test_mode=true")
    elif api_key.startswith(('sk-', 'sk-proj-')):
        print(f"   OpenAI API Key: ✅ Valid (ends with ...{api_key[-8:]})")
    else:
        print("   OpenAI API Key: ❌ Invalid format")
    
    print("\n📹 Camera & Detection Settings:")
    print(f"   Resolution: {app_settings.camera_width}x{app_settings.camera_height}")
    print(f"   Target FPS: {app_settings.target_fps}")
    print(f"   Confidence Threshold: {app_settings.confidence_threshold}")
    print(f"   IoU Threshold: {app_settings.iou_threshold}")
    
    print("\n⚡ Performance Settings:")
    print(f"   Frame Buffer Size: {app_settings.frame_buffer_size}")
    
    print("\n🔧 File Processing:")
    print(f"   URL Timeout: {focus_score_settings.url_timeout_seconds}s")
    print(f"   Max Retries: {focus_score_settings.max_retries}")
    print(f"   Retry Delay: {focus_score_settings.retry_delay_seconds}s")
    
    print("\n✅ Configuration verification complete!")
    print("\n🚀 To start the service:")
    print("   pipenv run python src/main_refactored.py")
    print("   # or")
    print(f"   pipenv run uvicorn src.main_refactored:app --host {app_settings.api_host} --port {app_settings.api_port} {'--reload' if app_settings.api_reload else ''}")

if __name__ == "__main__":
    main()
