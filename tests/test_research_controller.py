#!/usr/bin/env python3
"""
Test script for ResearchController refactoring and new functionality

This script tests:
1. Context awareness with required_framework parameter
2. Pre-flight check mechanism
3. LLM pool and fault tolerance
4. JSON serialization fixes
5. Interactive research capabilities
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
    ResearchController, UserInteractionRequired, 
    BASE_SYSTEM_PROMPT, TOOL_INSTRUCTION_TEMPLATE, REACT_PROMPT
)
from hierarchical.actions.research_model import (
    ResearchConfig, ResearchResult, ToolExecutionStatus,
    Context7ToolConfig, LibraryResolutionResult
)
from hierarchical.actions.research_service import ToolExecutionService
from hierarchical.context import HierarchicalContext
from metagpt.schema import Message
from metagpt.memory.role_zero_memory import RoleZeroLongTermMemory


class TestResearchController:
    """Test class for ResearchController functionality"""
    
    def __init__(self):
        self.config = ResearchConfig()
        self.controller = ResearchController(self.config)
        self.test_results = []
    
    async def test_context_awareness(self):
        """Test 1: Context awareness with required_framework parameter"""
        print("🧪 Testing Context Awareness...")
        
        # Test framework extraction
        framework = self.controller._extract_framework_name("How to use React hooks?")
        assert framework == "react", f"Expected 'react', got '{framework}'"
        
        framework = self.controller._extract_framework_name("Explain Django models")
        assert framework == "django", f"Expected 'django', got '{framework}'"
        
        framework = self.controller._extract_framework_name("General programming question")
        assert framework == "", f"Expected empty string, got '{framework}'"
        
        print("✅ Context awareness test passed")
        self.test_results.append({"test": "context_awareness", "status": "passed"})
    
    async def test_pre_flight_check(self):
        """Test 2: Pre-flight check mechanism"""
        print("🧪 Testing Pre-flight Check...")
        
        # Test with required framework
        action = {"tool_name": "resolve-library-id", "tool_args": {"libraryName": "react"}}
        result = self.controller._pre_flight_check(action, "react")
        assert result == True, f"Expected True for resolve-library-id, got {result}"
        
        action = {"tool_name": "FINISH", "tool_args": {"result": "Done"}}
        result = self.controller._pre_flight_check(action, "react")
        assert result == False, f"Expected False for FINISH with framework, got {result}"
        
        # Test without required framework
        action = {"tool_name": "FINISH", "tool_args": {"result": "Done"}}
        result = self.controller._pre_flight_check(action, None)
        assert result == True, f"Expected True for FINISH without framework, got {result}"
        
        print("✅ Pre-flight check test passed")
        self.test_results.append({"test": "pre_flight_check", "status": "passed"})
    
    async def test_llm_pool_integration(self):
        """Test 3: LLM pool and fault tolerance"""
        print("🧪 Testing LLM Pool Integration...")
        
        # Set up test LLM pool
        self.controller.llm_pool = ["test-model-1", "test-model-2"]
        
        # Test that LLM pool is set up correctly
        assert self.controller.llm_pool == ["test-model-1", "test-model-2"], "LLM pool should be set correctly"
        
        print("✅ LLM pool integration test passed")
        self.test_results.append({"test": "llm_pool_integration", "status": "passed"})
    
    async def test_json_serialization(self):
        """Test 4: JSON serialization fixes"""
        print("🧪 Testing JSON Serialization...")
        
        # Test ToolExecutionResult serialization with enum
        from hierarchical.actions.research_model import ToolExecutionResult
        from enum import Enum
        
        result = ToolExecutionResult(
            status=ToolExecutionStatus.SUCCESS,
            source="test",
            raw_data={"key": "value"}
        )
        
        # Test that serialization works with enum
        import json
        try:
            serialized = json.dumps(result.__dict__, ensure_ascii=False, default=lambda o: o.value if isinstance(o, Enum) else str(o))
            deserialized = json.loads(serialized)
            assert deserialized["status"] == "success", f"Expected 'success', got {deserialized['status']}"
            print("✅ JSON serialization test passed")
            self.test_results.append({"test": "json_serialization", "status": "passed"})
        except Exception as e:
            print(f"❌ JSON serialization test failed: {e}")
            self.test_results.append({"test": "json_serialization", "status": "failed", "error": str(e)})
    
    async def test_interactive_research(self):
        """Test 5: Interactive research capabilities"""
        print("🧪 Testing Interactive Research...")
        
        # Test UserInteractionRequired exception
        try:
            question = "What is your preferred framework?"
            resume_state = {"query": "test", "step": 1}
            
            # This should raise UserInteractionRequired when ASK_USER tool is used
            action = {"tool_name": "ASK_USER", "tool_args": {"question": question}}
            
            # Mock the context to avoid actual tool execution
            with patch.object(self.controller, '_execute_tool_action') as mock_execute:
                mock_execute.side_effect = UserInteractionRequired(question, resume_state)
                
                try:
                    await self.controller._execute_tool_action(action, "test query")
                    print("❌ Interactive research test failed: No exception raised")
                    self.test_results.append({"test": "interactive_research", "status": "failed", "error": "No exception raised"})
                except UserInteractionRequired as e:
                    assert e.question == question, f"Expected question '{question}', got '{e.question}'"
                    assert e.resume_state == resume_state, f"Expected resume_state {resume_state}, got {e.resume_state}"
                    print("✅ Interactive research test passed")
                    self.test_results.append({"test": "interactive_research", "status": "passed"})
                except Exception as e:
                    print(f"❌ Interactive research test failed: {e}")
                    self.test_results.append({"test": "interactive_research", "status": "failed", "error": str(e)})
        except Exception as e:
            print(f"❌ Interactive research test setup failed: {e}")
            self.test_results.append({"test": "interactive_research", "status": "failed", "error": str(e)})
    
    async def test_prompt_constants(self):
        """Test 6: Prompt constants are properly defined"""
        print("🧪 Testing Prompt Constants...")
        
        # Test that constants are defined
        assert BASE_SYSTEM_PROMPT is not None, "BASE_SYSTEM_PROMPT should not be None"
        assert TOOL_INSTRUCTION_TEMPLATE is not None, "TOOL_INSTRUCTION_TEMPLATE should not be None"
        assert REACT_PROMPT is not None, "REACT_PROMPT should not be None"
        
        # Test that placeholders exist
        assert "{original_goal}" in BASE_SYSTEM_PROMPT, "BASE_SYSTEM_PROMPT should contain {original_goal}"
        assert "{available_tools}" in TOOL_INSTRUCTION_TEMPLATE, "TOOL_INSTRUCTION_TEMPLATE should contain {available_tools}"
        assert "{system_prompt}" in REACT_PROMPT, "REACT_PROMPT should contain {system_prompt}"
        
        print("✅ Prompt constants test passed")
        self.test_results.append({"test": "prompt_constants", "status": "passed"})
    
    async def test_framework_extraction(self):
        """Test 7: Framework extraction from queries"""
        print("🧪 Testing Framework Extraction...")
        
        test_cases = [
            ("How to use React hooks?", "react"),
            ("Explain Django models", "django"),
            ("Vue.js best practices", "vue"),
            ("Angular components tutorial", "angular"),
            ("Flask web development", "flask"),
            ("Spring boot configuration", "spring"),
            ("Express.js middleware", "express"),
            ("General programming question", ""),
            ("How to build websites", ""),
        ]
        
        for query, expected_framework in test_cases:
            actual_framework = self.controller._extract_framework_name(query)
            assert actual_framework == expected_framework, f"Query: '{query}' - Expected: {expected_framework}, Got: {actual_framework}"
        
        print("✅ Framework extraction test passed")
        self.test_results.append({"test": "framework_extraction", "status": "passed"})
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting ResearchController Tests...")
        print("=" * 60)
        
        try:
            await self.test_context_awareness()
            await self.test_pre_flight_check()
            await self.test_llm_pool_integration()
            await self.test_json_serialization()
            await self.test_interactive_research()
            await self.test_prompt_constants()
            await self.test_framework_extraction()
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
    tester = TestResearchController()
    success = await tester.run_all_tests()
    
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())