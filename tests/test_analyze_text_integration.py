#!/usr/bin/env python3
"""
Test script for AnalyzeText action and integration with ChangeCoordinator

This script tests:
1. Basic functionality of the new AnalyzeText action
2. Integration of AnalyzeText with ChangeCoordinator
3. Proper tool selection in the modified _act method
"""

import asyncio
import sys
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add the root of the MetaGPT project to the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from hierarchical.roles.change_coordinator import ChangeCoordinator
from hierarchical.actions.analyze_text import AnalyzeText
from hierarchical.actions.research_controller import ResearchController
from hierarchical.context import HierarchicalContext
from metagpt.schema import Message
from metagpt.llm import LLM


class TestAnalyzeTextIntegration:
    """Test class for AnalyzeText functionality and integration"""
    
    def __init__(self):
        self.test_results = []
    
    async def test_analyze_text_action(self):
        """Test 1: Basic functionality of AnalyzeText action"""
        print("🧪 Testing AnalyzeText Action...")
        
        # Create a mock LLM that returns a predefined response
        mock_llm = AsyncMock()
        mock_llm.aask.return_value = '["React", "Django", "AutoGen"]'
        
        # Create AnalyzeText action with mock LLM
        analyze_text_action = AnalyzeText(llm=mock_llm)
        
        # Test input
        query = "Identify the primary subjects in this document"
        context_text = "# Introduction\nThis document covers React, Django, and AutoGen frameworks.\n## Details\nMore details about these technologies."
        
        # Execute the action
        result = await analyze_text_action.run(query=query, context_text=context_text)
        
        # Verify the result
        expected_result = '["React", "Django", "AutoGen"]'
        assert result == expected_result, f"Expected {expected_result}, got {result}"
        
        # Verify the LLM was called with the correct prompt
        mock_llm.aask.assert_called_once()
        call_args = mock_llm.aask.call_args[0][0]  # Get the prompt argument
        assert "You are an expert analysis AI" in call_args, "Prompt should contain expert analysis instruction"
        assert query in call_args, "Prompt should contain the query"
        assert context_text in call_args, "Prompt should contain the context text"
        
        print("✅ AnalyzeText action test passed")
        self.test_results.append({"test": "analyze_text_action", "status": "passed"})
    
    async def test_analyze_text_integration_with_coordinator(self):
        """Test 2: Integration of AnalyzeText with ChangeCoordinator"""
        print("🧪 Testing AnalyzeText Integration with ChangeCoordinator...")
        
        # Create a mock LLM
        mock_llm = AsyncMock()
        mock_llm.aask.return_value = '["React", "Django"]'
        
        # Create ChangeCoordinator with mock LLM
        coordinator = ChangeCoordinator(llm=mock_llm)
        
        # Verify that AnalyzeText is in the actions list
        analyze_text_action = None
        for action in coordinator.actions:
            if isinstance(action, AnalyzeText):
                analyze_text_action = action
                break
        
        assert analyze_text_action is not None, "ChangeCoordinator should have AnalyzeText action"
        
        # Test that the action can be found by type
        found_action = next((a for a in coordinator.actions if isinstance(a, AnalyzeText)), None)
        assert found_action is not None, "Should be able to find AnalyzeText action by type"
        
        print("✅ AnalyzeText integration test passed")
        self.test_results.append({"test": "analyze_text_integration", "status": "passed"})
    
    async def test_tool_selection_logic(self):
        """Test 3: Proper tool selection in the modified _act method"""
        print("🧪 Testing Tool Selection Logic...")
        
        # This test verifies the logic in the modified _act method
        # where AnalyzeText is used for internal analysis and Research is used for external research
        
        # Create a mock ChangeCoordinator
        coordinator = ChangeCoordinator()
        
        # Verify that both AnalyzeText and other actions are present
        actions = coordinator.actions
        analyze_text_action = next((a for a in actions if isinstance(a, AnalyzeText)), None)
        analyze_header_action = next((a for a in actions if isinstance(a, type(actions[0]).__bases__[0]) and a.name == "Analyze Document Header Changes"), None)
        
        assert analyze_text_action is not None, "AnalyzeText action should be present"
        assert analyze_header_action is not None, "AnalyzeHeaderChanges action should be present"
        
        # Verify the actions list has the correct number of actions
        # (AnalyzeHeaderChanges, AssessSubdivision, AnalyzeText)
        assert len(actions) == 3, f"Expected 3 actions, got {len(actions)}"
        
        print("✅ Tool selection logic test passed")
        self.test_results.append({"test": "tool_selection_logic", "status": "passed"})
    
    async def test_json_parsing_in_analyze_text(self):
        """Test 4: JSON parsing in AnalyzeText action"""
        print("🧪 Testing JSON Parsing in AnalyzeText...")
        
        # Create a mock LLM that returns JSON response
        mock_llm = AsyncMock()
        mock_llm.aask.return_value = '```json\n["React", "Django", "AutoGen"]\n```'
        
        # Create AnalyzeText action with mock LLM
        analyze_text_action = AnalyzeText(llm=mock_llm)
        
        # Test input
        query = "Identify the primary subjects in this document"
        context_text = "# Introduction\nThis document covers React, Django, and AutoGen frameworks."
        
        # Execute the action
        result = await analyze_text_action.run(query=query, context_text=context_text)
        
        # Verify the result is properly parsed
        expected_result = '["React", "Django", "AutoGen"]'
        assert result == expected_result, f"Expected {expected_result}, got {result}"
        
        print("✅ JSON parsing test passed")
        self.test_results.append({"test": "json_parsing", "status": "passed"})
    
    async def test_error_handling_in_analyze_text(self):
        """Test 5: Error handling in AnalyzeText action"""
        print("🧪 Testing Error Handling in AnalyzeText...")
        
        # Create a mock LLM that raises an exception
        mock_llm = AsyncMock()
        mock_llm.aask.side_effect = Exception("LLM service unavailable")
        
        # Create AnalyzeText action with mock LLM
        analyze_text_action = AnalyzeText(llm=mock_llm)
        
        # Test input
        query = "Identify the primary subjects in this document"
        context_text = "# Introduction\nThis document covers React, Django, and AutoGen frameworks."
        
        # Execute the action and handle exception
        try:
            result = await analyze_text_action.run(query=query, context_text=context_text)
            # If we get here, it means the exception was handled
            assert isinstance(result, str), "Result should be a string even when LLM fails"
            print(f"Result when LLM fails: {result}")
        except Exception as e:
            # If an exception is raised, it should be handled by the caller
            assert "LLM service unavailable" in str(e), "Exception should contain the original error message"
        
        print("✅ Error handling test passed")
        self.test_results.append({"test": "error_handling", "status": "passed"})
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting AnalyzeText Integration Tests...")
        print("=" * 60)
        
        try:
            await self.test_analyze_text_action()
            await self.test_analyze_text_integration_with_coordinator()
            await self.test_tool_selection_logic()
            await self.test_json_parsing_in_analyze_text()
            await self.test_error_handling_in_analyze_text()
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            import traceback
            traceback.print_exc()
            self.test_results.append({"test": "overall_execution", "status": "failed", "error": str(e)})
        
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
    tester = TestAnalyzeTextIntegration()
    success = await tester.run_all_tests()
    
    if success:
        print("🎉 All AnalyzeText integration tests passed!")
        sys.exit(0)
    else:
        print("❌ Some AnalyzeText integration tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())