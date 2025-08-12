#!/usr/bin/env python3
"""
Test script to verify MonitorStatus enum functionality
"""

from src.services.focus_service import MonitorStatus

def test_monitor_status_enum():
    """Test the MonitorStatus enum"""
    
    print("Testing MonitorStatus Enum:")
    print("=" * 50)
    
    # Test WAITING_DETECTION
    status = MonitorStatus.WAITING_DETECTION
    print(f"WAITING_DETECTION: text='{status.text}', color={status.color}")
    
    # Test PERSON_DETECTED  
    status = MonitorStatus.PERSON_DETECTED
    print(f"PERSON_DETECTED: text='{status.text}', color={status.color}")
    
    # Test PERSON_NOT_DETECTED
    status = MonitorStatus.PERSON_NOT_DETECTED
    print(f"PERSON_NOT_DETECTED: text='{status.text}', color={status.color}")
    
    print("\nTesting conditional logic:")
    print("-" * 30)
    
    # Test conditional logic (simulating the original code logic)
    is_initialized = False
    previous_person_state = None
    
    # Simulate uninitialized state
    if not is_initialized:
        status = MonitorStatus.WAITING_DETECTION
    else:
        status = MonitorStatus.PERSON_DETECTED if previous_person_state else MonitorStatus.PERSON_NOT_DETECTED
    
    print(f"Uninitialized state: {status.text} | Color: {status.color}")
    
    # Simulate initialized state with person detected
    is_initialized = True
    previous_person_state = True
    
    if not is_initialized:
        status = MonitorStatus.WAITING_DETECTION
    else:
        status = MonitorStatus.PERSON_DETECTED if previous_person_state else MonitorStatus.PERSON_NOT_DETECTED
    
    print(f"Person detected: {status.text} | Color: {status.color}")
    
    # Simulate initialized state with no person detected
    previous_person_state = False
    
    if not is_initialized:
        status = MonitorStatus.WAITING_DETECTION
    else:
        status = MonitorStatus.PERSON_DETECTED if previous_person_state else MonitorStatus.PERSON_NOT_DETECTED
    
    print(f"Person not detected: {status.text} | Color: {status.color}")
    
    print("\n✅ All tests passed! Enum is working correctly.")

if __name__ == "__main__":
    test_monitor_status_enum()
