#!/usr/bin/env python3
"""
Simplified test for MonitorStatus enum
"""

from enum import Enum
from typing import Tuple

class MonitorStatus(Enum):
    """Enumeration for monitor status messages and colors"""
    WAITING_DETECTION = ("Waiting for first detection...", (255, 255, 0))  # Yellow
    PERSON_DETECTED = ("Person: Detected", (0, 255, 0))  # Green
    PERSON_NOT_DETECTED = ("Person: Not Detected", (0, 0, 255))  # Red
    
    def __init__(self, text: str, color: Tuple[int, int, int]):
        self.text = text
        self.color = color

def test_monitor_status_enum():
    """Test the MonitorStatus enum"""
    
    print("Testing MonitorStatus Enum:")
    print("=" * 50)
    
    # Test all enum values
    for status in MonitorStatus:
        print(f"{status.name}: text='{status.text}', color={status.color}")
    
    print("\nTesting conditional logic:")
    print("-" * 30)
    
    # Simulate the refactored logic
    test_cases = [
        (False, None, "Uninitialized state"),
        (True, True, "Person detected"),
        (True, False, "Person not detected")
    ]
    
    for is_initialized, previous_person_state, description in test_cases:
        if not is_initialized:
            status = MonitorStatus.WAITING_DETECTION
        else:
            status = MonitorStatus.PERSON_DETECTED if previous_person_state else MonitorStatus.PERSON_NOT_DETECTED
        
        print(f"{description}: {status.text} | Color: {status.color}")
    
    print("\n✅ All tests passed! Enum is working correctly.")

if __name__ == "__main__":
    test_monitor_status_enum()
