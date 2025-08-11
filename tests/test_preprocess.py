#!/usr/bin/env python3
"""
Test script for _preprocess_decision_string method
"""

import sys
from pathlib import Path

# Add the root of the MetaGPT project to the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import the actual method from the module
from hierarchical.actions.research_controller import ResearchController

# Create an instance to access the method
controller = ResearchController()

def test_preprocess_method():
    """Test the preprocess method with various inputs"""
    print("🧪 Testing _preprocess_decision_string method...")
    
    # Test case 1: Normal JSON
    input1 = '{"thought": "test", "action": {"tool_name": "resolve-library-id"}}'
    result1 = controller._preprocess_decision_string(input1)
    print(f"Input 1: {input1}")
    print(f"Output 1: {result1}")
    
    # Test case 2: JSON with extra quotes around tool_name value
    input2 = '{"thought": "test", "action": {"tool_name": ""tool_name""}}'
    result2 = controller._preprocess_decision_string(input2)
    print(f"Input 2: {input2}")
    print(f"Output 2: {result2}")
    
    # Test case 3: Just the problematic string
    input3 = '"tool_name"'
    result3 = controller._preprocess_decision_string(input3)
    print(f"Input 3: {input3}")
    print(f"Output 3: {result3}")
    
    # Test case 4: String with outer quotes
    input4 = '"""tool_name"""'
    result4 = controller._preprocess_decision_string(input4)
    print(f"Input 4: {input4}")
    print(f"Output 4: {result4}")
    
    # Test case 5: Common LLM output format with markdown
    input5 = '```json\n{\n  "thought": "I need to resolve the library name",\n  "action": {\n    "tool_name": "resolve-library-id",\n    "tool_args": {"libraryName": "React"}\n  }\n}\n```'
    result5 = controller._preprocess_decision_string(input5)
    print(f"Input 5: {input5}")
    print(f"Output 5: {result5}")
    
    # Test case 6: String with single quotes
    input6 = "{'thought': 'test', 'action': {'tool_name': 'resolve-library-id'}}"
    result6 = controller._preprocess_decision_string(input6)
    print(f"Input 6: {input6}")
    print(f"Output 6: {result6}")

if __name__ == "__main__":
    test_preprocess_method()