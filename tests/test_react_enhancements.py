#!/usr/bin/env python3
"""
Test script for ReAct enhancements in ResearchController
"""

import asyncio
import sys
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add the root of the MetaGPT project to the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from hierarchical.actions.research_controller import (
    ResearchController, ReActParseError, REACT_PROMPT
)
from hierarchical.actions.research_model import ResearchConfig

class TestReActEnhancements:
    """Test class for ReAct enhancements"""
    
    def __init__(self):
        self.config = ResearchConfig()
        self.controller = ResearchController(self.config)
        self.test_results = []
    
    async def test_react_parse_error(self):
        """Test ReActParseError class functionality"""
        print("🧪 Testing ReActParseError...")
        
        # Test ReActParseError creation
        error = ReActParseError("TEST_ERROR", "This is a test error", True)
        assert error.error_type == "TEST_ERROR"
        assert "TEST_ERROR" in str(error)
        assert "This is a test error" in str(error)
        assert error.recoverable == True
        
        # Test ReActParseError with default recoverable value
        error2 = ReActParseError("TEST_ERROR2", "This is another test error")
        assert error2.recoverable == True
        
        print("✅ ReActParseError test passed")
        self.test_results.append({"test": "react_parse_error", "status": "passed"})
    
    async def test_react_cycle_state(self):
        """Test ReActCycleState class functionality"""
        print("🧪 Testing ReActCycleState...")
        
        # Create a ReActCycleState instance
        cycle_state = self.controller.ReActCycleState(max_retries=2)
        assert cycle_state.max_parse_retries == 2
        assert cycle_state.parse_retry_count == 0
        assert len(cycle_state.error_history) == 0
        
        # Test logging errors
        error1 = ReActParseError("ERROR_TYPE_1", "First error")
        cycle_state.log_error(error1)
        assert cycle_state.parse_retry_count == 1
        assert len(cycle_state.error_history) == 1
        assert cycle_state.error_history[0] == "ERROR_TYPE_1"
        
        # Test should_retry with recoverable error
        assert cycle_state.should_retry(error1) == True
        
        # Test logging another error of the same type
        error2 = ReActParseError("ERROR_TYPE_1", "Second error")
        cycle_state.log_error(error2)
        assert cycle_state.parse_retry_count == 2
        
        # Test loop detection (should not retry when same error type occurs twice)
        assert cycle_state.should_retry(error2) == False
        
        # Test with unrecoverable error
        error3 = ReActParseError("ERROR_TYPE_3", "Third error", False)
        assert cycle_state.should_retry(error3) == False
        
        print("✅ ReActCycleState test passed")
        self.test_results.append({"test": "react_cycle_state", "status": "passed"})
    
    async def test_react_prompt(self):
        """Test REACT_PROMPT template"""
        print("🧪 Testing REACT_PROMPT...")
        
        # Test that REACT_PROMPT is defined
        assert REACT_PROMPT is not None, "REACT_PROMPT should not be None"
        
        # Test that placeholders exist in REACT_PROMPT
        assert "{system_prompt}" in REACT_PROMPT, "REACT_PROMPT should contain {system_prompt}"
        assert "{tool_instruction}" in REACT_PROMPT, "REACT_PROMPT should contain {tool_instruction}"
        assert "{scratchpad}" in REACT_PROMPT, "REACT_PROMPT should contain {scratchpad}"
        
        print("✅ REACT_PROMPT test passed")
        self.test_results.append({"test": "react_prompt", "status": "passed"})
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting ReAct Enhancements Tests...")
        print("=" * 60)
        
        try:
            await self.test_react_parse_error()
            await self.test_react_cycle_state()
            await self.test_react_prompt()
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            import traceback
            traceback.print_exc()
        
        print("=" * 60)
        print("📊 Test Results Summary:")
        
        passed = sum(1 for result in self.test_results if result["status"] == "passed")
        failed = sum(1 for result in self.test_results if result["status"] == "failed")
        skipped = sum(1 for result in self.test_results if result["status"] == "skipped")
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Skipped: {skipped}")
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
    tester = TestReActEnhancements()
    success = await tester.run_all_tests()
    
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())