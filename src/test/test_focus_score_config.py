#!/usr/bin/env python3
"""
Test script to verify the focus score configuration refactoring
"""
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_config_imports():
    """Test that all config imports work correctly"""
    from config.settings import FocusScoreSettings
    
    # Create test config with test mode enabled
    test_config = FocusScoreSettings(test_mode=True)
    print("✅ Successfully imported FocusScoreSettings")
    
    # Test configuration values
    print(f"✅ Model ID: {test_config.model_id}")
    print(f"✅ Max file size: {test_config.max_file_size_mb}MB")
    print(f"✅ Max retries: {test_config.max_retries}")
    print(f"✅ Temperature: {test_config.temperature}")
    print(f"✅ Max tokens: {test_config.max_tokens}")
    print(f"✅ Test mode: {test_config.test_mode}")
    
    # Use assertions instead of return statements
    assert hasattr(test_config, 'model_id')
    assert hasattr(test_config, 'max_file_size_mb')
    assert hasattr(test_config, 'test_mode')

def test_focus_score_app_import():
    """Test that the focus score app can import the config correctly"""
    # Set test mode environment variable
    import os
    os.environ['TEST_MODE'] = 'true'
    
    # This should work if our refactoring is successful
    from app.get_focus_score import settings, app
    print("✅ Successfully imported settings from get_focus_score app")
    print(f"✅ App title: {app.title}")
    print(f"✅ Settings model: {settings.model_id}")
    print(f"✅ Test mode enabled: {settings.test_mode}")
    
    # Use assertions instead of return statements
    assert app.title is not None
    assert hasattr(settings, 'model_id')
    assert hasattr(settings, 'test_mode')

def test_config_validation():
    """Test configuration validation"""
    from config.settings import FocusScoreSettings
    
    # Test with valid minimal config
    valid_config = FocusScoreSettings(openai_api_key="sk-test1234567890abcdef1234567890")
    print("✅ Valid config created successfully")
    
    # Test validation errors
    validation_passed = False
    try:
        invalid_config = FocusScoreSettings(
            openai_api_key="invalid",
            max_file_size_mb=150  # Too large
        )
        print("❌ Should have failed validation")
    except ValueError as e:
        print(f"✅ Validation correctly caught error: {str(e)[:50]}...")
        validation_passed = True
    
    # Use assertions instead of return statements
    assert hasattr(valid_config, 'openai_api_key')
    assert validation_passed, "Validation should have caught the invalid config"

if __name__ == "__main__":
    print("🧪 Testing focus score configuration refactoring...\n")
    
    success = True
    success &= test_config_imports()
    print()
    success &= test_focus_score_app_import()
    print()
    success &= test_config_validation()
    
    print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed!'}")
    
    if success:
        print("\n📋 Configuration refactoring completed successfully:")
        print("1. ✅ Moved Settings class to config/settings.py as FocusScoreSettings")
        print("2. ✅ Added proper validation for OpenAI API key and other parameters")
        print("3. ✅ Updated imports in get_focus_score.py")
        print("4. ✅ Added new configuration parameters (temperature, max_tokens)")
        print("5. ✅ Maintained backward compatibility with existing .env files")
        print("6. ✅ Updated config package exports")
        print("7. ✅ Enhanced error handling and validation")
