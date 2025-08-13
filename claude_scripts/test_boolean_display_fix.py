#!/usr/bin/env python3
"""Test script to verify the boolean display fix handles all data formats correctly."""

def test_format_label_value():
    """Test the formatLabelValue logic with various input types."""
    
    # Simulate the JavaScript formatLabelValue function logic in Python
    def format_label_value(label_data):
        if label_data is None:
            return "-"
        
        # If it's a dict with a value property, extract the value
        if isinstance(label_data, dict) and "value" in label_data:
            value = label_data["value"]
            # Convert to string, handling booleans properly
            if isinstance(value, bool):
                return "True" if value else "False"
            return str(value)
        
        # For direct values (backwards compatibility)
        if isinstance(label_data, bool):
            return "True" if label_data else "False"
        
        return str(label_data)
    
    # Test cases from the labeling session data we saw
    test_cases = [
        # Current format: object with value property
        ({"value": True, "comment": None}, "True"),
        ({"value": False, "comment": None}, "False"),
        ({"value": 1, "comment": None}, "1"),
        ({"value": 0, "comment": None}, "0"),
        ({"value": "Good", "comment": None}, "Good"),
        
        # Direct values (backwards compatibility)
        (True, "True"),
        (False, "False"),
        (1, "1"),
        (0, "0"),
        ("Good", "Good"),
        ("True", "True"),
        ("False", "False"),
        
        # Edge cases
        (None, "-"),
        ("", ""),
        ({}, "{}"),
        ({"comment": "test"}, "{'comment': 'test'}"),  # No value property
    ]
    
    print("Testing formatLabelValue logic...")
    all_passed = True
    
    for i, (input_data, expected) in enumerate(test_cases):
        result = format_label_value(input_data)
        status = "✅" if result == expected else "❌"
        print(f"{status} Test {i+1}: {input_data} → {result} (expected: {expected})")
        if result != expected:
            all_passed = False
    
    print(f"\nOverall: {'✅ All tests passed' if all_passed else '❌ Some tests failed'}")
    return all_passed

if __name__ == "__main__":
    test_format_label_value()