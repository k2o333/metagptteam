#!/usr/bin/env python3
"""
Test script for _validate_action_params method enhancements
"""

import asyncio
import sys
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add the root of the MetaGPT project to the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from hierarchical.actions.research_controller import ResearchController
from hierarchical.actions.research_model import ResearchConfig


class TestValidateActionParams:
    """Test class for _validate_action_params method enhancements"""
    
    def __init__(self):
        self.config = ResearchConfig()
        self.controller = ResearchController(self.config)
        self.test_results = []
    
    def test_tool_name_validation(self):
        """Test tool_name validation and cleaning"""
        print("🧪 Testing Tool Name Validation...")
        
        # Test 1: Valid tool_name
        action = {"tool_name": "resolve-library-id", "tool_args": {}}
        mcp_manager = Mock()
        mcp_manager.get_tool_schema.return_value = None  # No schema for simplicity
        
        is_valid, message = self.controller._validate_action_params(action, mcp_manager)
        assert is_valid == True, f"Expected True for valid tool_name, got {is_valid}"
        assert message == "Schema not available.", f"Expected 'Schema not available.', got '{message}'"
        
        # Test 2: Missing tool_name
        action = {"tool_args": {}}
        is_valid, message = self.controller._validate_action_params(action, mcp_manager)
        assert is_valid == False, f"Expected False for missing tool_name, got {is_valid}"
        assert "missing 'tool_name'" in message, f"Expected message about missing tool_name, got '{message}'"
        
        # Test 3: Malformed tool_name with extra quotes
        action = {"tool_name": '"resolve-library-id"', "tool_args": {}}
        is_valid, message = self.controller._validate_action_params(action, mcp_manager)
        assert is_valid == True, f"Expected True after cleaning tool_name, got {is_valid}"
        assert action["tool_name"] == "resolve-library-id", f"Expected cleaned tool_name, got '{action['tool_name']}'"
        
        # Test 4: Placeholder tool_name
        action = {"tool_name": "tool_name", "tool_args": {}}
        is_valid, message = self.controller._validate_action_params(action, mcp_manager)
        assert is_valid == False, f"Expected False for placeholder tool_name, got {is_valid}"
        assert "placeholder or malformed" in message, f"Expected message about placeholder, got '{message}'"
        
        # Test 5: FINISH tool
        action = {"tool_name": "FINISH", "tool_args": {}}
        is_valid, message = self.controller._validate_action_params(action, mcp_manager)
        assert is_valid == True, f"Expected True for FINISH tool, got {is_valid}"
        assert "No validation needed" in message, f"Expected message about no validation, got '{message}'"
        
        print("✅ Tool name validation test passed")
        self.test_results.append({"test": "tool_name_validation", "status": "passed"})
    
    def test_parameter_case_insensitivity(self):
        """Test parameter case insensitivity handling"""
        print("🧪 Testing Parameter Case Insensitivity...")
        
        # Mock schema with required parameters
        schema = {
            "required": ["libraryName"],
            "properties": {
                "libraryName": {"type": "string"}
            }
        }
        
        mcp_manager = Mock()
        mcp_manager.get_tool_schema.return_value = schema
        
        # Test 1: Correct case
        action = {"tool_name": "resolve-library-id", "tool_args": {"libraryName": "React"}}
        is_valid, message = self.controller._validate_action_params(action, mcp_manager)
        assert is_valid == True, f"Expected True for correct case, got {is_valid}"
        
        # Test 2: Wrong case should be corrected
        action = {"tool_name": "resolve-library-id", "tool_args": {"libraryname": "React"}}  # lowercase 'n'
        is_valid, message = self.controller._validate_action_params(action, mcp_manager)
        assert is_valid == True, f"Expected True after case correction, got {is_valid}"
        assert "libraryName" in action["tool_args"], "Expected corrected parameter name"
        assert action["tool_args"]["libraryName"] == "React", f"Expected 'React', got '{action['tool_args']['libraryName']}'"
        
        print("✅ Parameter case insensitivity test passed")
        self.test_results.append({"test": "parameter_case_insensitivity", "status": "passed"})
    
    def test_missing_parameters(self):
        """Test missing parameters detection"""
        print("🧪 Testing Missing Parameters Detection...")
        
        # Mock schema with required parameters
        schema = {
            "required": ["libraryName", "topic"],
            "properties": {
                "libraryName": {"type": "string"},
                "topic": {"type": "string"}
            }
        }
        
        mcp_manager = Mock()
        mcp_manager.get_tool_schema.return_value = schema
        
        # Test 1: Missing both parameters
        action = {"tool_name": "get-library-docs", "tool_args": {}}
        is_valid, message = self.controller._validate_action_params(action, mcp_manager)
        assert is_valid == False, f"Expected False for missing parameters, got {is_valid}"
        assert "missing required parameters" in message, f"Expected message about missing parameters, got '{message}'"
        assert "libraryName" in message, f"Expected 'libraryName' in message, got '{message}'"
        assert "topic" in message, f"Expected 'topic' in message, got '{message}'"
        
        # Test 2: Missing one parameter
        action = {"tool_name": "get-library-docs", "tool_args": {"libraryName": "React"}}
        is_valid, message = self.controller._validate_action_params(action, mcp_manager)
        assert is_valid == False, f"Expected False for missing parameter, got {is_valid}"
        assert "topic" in message, f"Expected 'topic' in message, got '{message}'"
        assert "libraryName" not in message, f"Did not expect 'libraryName' in message, got '{message}'"
        
        print("✅ Missing parameters detection test passed")
        self.test_results.append({"test": "missing_parameters", "status": "passed"})
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting _validate_action_params Tests...")
        print("=" * 60)
        
        try:
            self.test_tool_name_validation()
            self.test_parameter_case_insensitivity()
            self.test_missing_parameters()
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            import traceback
            traceback.print_exc()
        
        print("=" * 60)
        print("📊 Test Results Summary:")
        
        passed = sum(1 for result in self.test_results if result["status"] == "passed")
        failed = sum(1 for result in self.test_results if result["status"] == "failed")
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Total: {len(self.test_results)}")
        
        if failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if result["status"] == "failed":
                    print(f"  - {result['test']}: {result.get('error', 'Unknown error')}")
        
        print("=" * 60)
        return failed == 0


async def main():
    """Main test function"""
    tester = TestValidateActionParams()
    success = tester.run_all_tests()
    
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())