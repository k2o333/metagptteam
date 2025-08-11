#!/usr/bin/env python3
"""
Test script for _validate_parsed_result method enhancements
"""

import sys
from pathlib import Path
import logging

# Add the root of the MetaGPT project to the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Setup logging
logging.basicConfig(level=logging.WARNING)

def _validate_parsed_result(thought: str, action: dict) -> bool:
    """验证解析结果"""
    # 基本类型检查
    if not isinstance(thought, str) or not isinstance(action, dict):
        return False
        
    # 检查并清理action中的tool_name
    tool_name = action.get("tool_name")
    if tool_name is not None:
        # 如果tool_name存在，它应该是一个字符串
        if not isinstance(tool_name, str):
            return False
            
        # 如果tool_name是带引号的字符串，则清理它
        if tool_name.startswith('"') and tool_name.endswith('"') and len(tool_name) > 1:
            clean_tool_name = tool_name.strip('"')
            action["tool_name"] = clean_tool_name
            print(f"Corrected malformed tool_name from '{tool_name}' to '{clean_tool_name}'")
        elif tool_name.startswith("'") and tool_name.endswith("'") and len(tool_name) > 1:
            clean_tool_name = tool_name.strip("'")
            action["tool_name"] = clean_tool_name
            print(f"Corrected malformed tool_name from '{tool_name}' to '{clean_tool_name}'")
        # 如果清理后的tool_name仍然是"tool_name"字面量，则无效
        if action.get("tool_name") == "tool_name":
            return False
    
    return True

def test_validate_parsed_result():
    """Test the validate_parsed_result method with various inputs"""
    print("🧪 Testing _validate_parsed_result method...")
    
    # Test case 1: Valid thought and action
    thought1 = "This is a valid thought"
    action1 = {"tool_name": "resolve-library-id"}
    result1 = _validate_parsed_result(thought1, action1)
    print(f"Test 1 - Valid input: {result1} (Expected: True)")
    assert result1 == True, f"Expected True, got {result1}"
    assert action1["tool_name"] == "resolve-library-id", f"Expected 'resolve-library-id', got '{action1['tool_name']}'"
    
    # Test case 2: Invalid thought type
    thought2 = 123
    action2 = {"tool_name": "resolve-library-id"}
    result2 = _validate_parsed_result(thought2, action2)
    print(f"Test 2 - Invalid thought type: {result2} (Expected: False)")
    assert result2 == False, f"Expected False, got {result2}"
    
    # Test case 3: Invalid action type
    thought3 = "This is a valid thought"
    action3 = "invalid_action"
    result3 = _validate_parsed_result(thought3, action3)
    print(f"Test 3 - Invalid action type: {result3} (Expected: False)")
    assert result3 == False, f"Expected False, got {result3}"
    
    # Test case 4: Valid action with no tool_name
    thought4 = "This is a valid thought"
    action4 = {"other_key": "some_value"}
    result4 = _validate_parsed_result(thought4, action4)
    print(f"Test 4 - Valid action with no tool_name: {result4} (Expected: True)")
    assert result4 == True, f"Expected True, got {result4}"
    
    # Test case 5: Invalid tool_name with double quotes (should be cleaned)
    thought5 = "This is a valid thought"
    action5 = {"tool_name": '"tool_name"'}
    result5 = _validate_parsed_result(thought5, action5)
    print(f"Test 5 - Invalid tool_name with double quotes: {result5} (Expected: False)")
    assert result5 == False, f"Expected False, got {result5}"
    assert action5["tool_name"] == "tool_name", f"Expected 'tool_name', got '{action5['tool_name']}'"
    
    # Test case 6: Invalid tool_name with single quotes (should be cleaned)
    thought6 = "This is a valid thought"
    action6 = {"tool_name": "'resolve-library-id'"}
    result6 = _validate_parsed_result(thought6, action6)
    print(f"Test 6 - Invalid tool_name with single quotes: {result6} (Expected: True)")
    assert result6 == True, f"Expected True, got {result6}"
    assert action6["tool_name"] == "resolve-library-id", f"Expected 'resolve-library-id', got '{action6['tool_name']}'"
    
    # Test case 7: Valid tool_name without quotes
    thought7 = "This is a valid thought"
    action7 = {"tool_name": "tool_name"}
    result7 = _validate_parsed_result(thought7, action7)
    print(f"Test 7 - Valid tool_name without quotes: {result7} (Expected: False)")
    assert result7 == False, f"Expected False, got {result7}"
    
    print("✅ All tests passed!")

if __name__ == "__main__":
    test_validate_parsed_result()