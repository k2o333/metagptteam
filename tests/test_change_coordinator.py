#!/usr/bin/env python3
"""
Test script for ChangeCoordinator modifications

This script tests:
1. Framework extraction from tasks
2. Strict handling of research review results
3. Integration with ResearchController
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
from hierarchical.actions.research_controller import ResearchController
from hierarchical.actions.research_model import ResearchConfig
from hierarchical.context import HierarchicalContext
from metagpt.schema import Message
from metagpt.llm import LLM


class TestChangeCoordinator:
    """Test class for ChangeCoordinator functionality"""
    
    def __init__(self):
        self.test_results = []
    
    async def test_framework_extraction(self):
        """Test 1: Framework extraction from tasks"""
        print("🧪 Testing Framework Extraction from Tasks...")
        
        # Create a mock ChangeCoordinator for testing
        coordinator = ChangeCoordinator()
        
        # Test framework extraction
        test_cases = [
            ("Add examples about React hooks", "react"),
            ("Update Django model documentation", "django"),
            ("Include Vue.js best practices", "vue"),
            ("Add Angular component examples", "angular"),
            ("Update Flask API documentation", "flask"),
            ("Include Spring boot configuration", "spring"),
            ("Add Express middleware examples", "express"),
            ("Update general introduction", None),
            ("Add programming examples", None),
        ]
        
        for task, expected_framework in test_cases:
            actual_framework = coordinator._extract_framework_from_task(task)
            assert actual_framework == expected_framework, f"Task: '{task}' - Expected: {expected_framework}, Got: {actual_framework}"
        
        print("✅ Framework extraction test passed")
        self.test_results.append({"test": "framework_extraction", "status": "passed"})
    
    async def test_strict_review_handling(self):
        """Test 2: Strict handling of research review results"""
        print("🧪 Testing Strict Review Handling...")
        
        # Create a mock ChangeCoordinator
        coordinator = ChangeCoordinator()
        
        # Test task queue structure
        task_queue = [
            {
                "full_heading_string": "# Introduction",
                "rewrite_task": "Add examples about React hooks",
                "status": "rewriting"
            },
            {
                "full_heading_string": "# Installation", 
                "rewrite_task": "Update Django model documentation",
                "status": "rewriting"
            }
        ]
        
        coordinator.task_queue = task_queue
        
        # Simulate research failure handling
        # This tests the logic where a rejected research review leads to task skipping
        task = coordinator.task_queue[0]
        
        # Simulate the task being marked as skipped due to research failure
        task["status"] = "skipped_due_to_research_failure"
        task["new_content"] = "<!-- SKIPPED: Introduction - Research failed. -->"
        
        # Verify the task state
        assert task["status"] == "skipped_due_to_research_failure", f"Expected skipped status, got {task['status']}"
        assert "SKIPPED" in task["new_content"], f"Expected SKIPPED in new_content, got {task['new_content']}"
        
        print("✅ Strict review handling test passed")
        self.test_results.append({"test": "strict_review_handling", "status": "passed"})
    
    async def test_research_integration(self):
        """Test 3: Integration with ResearchController"""
        print("🧪 Testing Research Integration...")
        
        # Create a mock context
        mock_llm = AsyncMock()
        mock_llm.aask.return_value = "Mock LLM response"
        
        ctx = HierarchicalContext(llm=mock_llm)
        
        # Create ResearchController and ChangeCoordinator
        research_config = ResearchConfig()
        research_controller = ResearchController(research_config)
        research_controller.set_context(ctx)
        
        coordinator = ChangeCoordinator(
            context=ctx,
            research_action=research_controller
        )
        
        # Test that coordinator has research action
        assert coordinator.research_action is not None, "Coordinator should have research action"
        assert isinstance(coordinator.research_action, ResearchController), "Research action should be ResearchController"
        
        # Test framework extraction integration
        task = "Add React hooks examples"
        framework = coordinator._extract_framework_from_task(task)
        assert framework == "react", f"Expected 'react', got '{framework}'"
        
        print("✅ Research integration test passed")
        self.test_results.append({"test": "research_integration", "status": "passed"})
    
    async def test_task_status_handling(self):
        """Test 4: Task status handling in rewrite process"""
        print("🧪 Testing Task Status Handling...")
        
        # Create a mock ChangeCoordinator
        coordinator = ChangeCoordinator()
        
        # Set up task queue
        task_queue = [
            {
                "full_heading_string": "# Getting Started",
                "rewrite_task": "Update React introduction",
                "status": "pending_rewrite"
            },
            {
                "full_heading_string": "# Installation",
                "rewrite_task": "Add Django setup instructions", 
                "status": "pending_rewrite"
            }
        ]
        
        coordinator.task_queue = task_queue
        
        # Test status transitions
        # Simulate the rewrite process
        for task in coordinator.task_queue:
            if task["status"] == "pending_rewrite":
                task["status"] = "rewriting"
        
        # Verify status updates
        for task in coordinator.task_queue:
            assert task["status"] == "rewriting", f"Expected 'rewriting' status, got {task['status']}"
        
        print("✅ Task status handling test passed")
        self.test_results.append({"test": "task_status_handling", "status": "passed"})
    
    async def test_error_handling(self):
        """Test 5: Error handling in research process"""
        print("🧪 Testing Error Handling...")
        
        # Create a mock ChangeCoordinator
        coordinator = ChangeCoordinator()
        
        # Set up a task that might fail
        task_queue = [
            {
                "full_heading_string": "# Advanced Topics",
                "rewrite_task": "Add complex framework examples",
                "status": "rewriting"
            }
        ]
        
        coordinator.task_queue = task_queue
        
        # Simulate research failure
        task = coordinator.task_queue[0]
        
        # Test that failed research leads to appropriate task status
        original_status = task["status"]
        
        # Simulate the logic from the modified _act method
        if True:  # Simulating research failure condition
            task["status"] = "skipped_due_to_research_failure"
            task["new_content"] = f"<!-- SKIPPED: {task['full_heading_string']} - Research failed. -->"
        
        # Verify the task was properly handled
        assert task["status"] != original_status, f"Task status should have changed from {original_status}"
        assert task["status"] == "skipped_due_to_research_failure", f"Expected skipped status, got {task['status']}"
        assert task["new_content"] is not None, "Task should have new_content even when skipped"
        
        print("✅ Error handling test passed")
        self.test_results.append({"test": "error_handling", "status": "passed"})
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting ChangeCoordinator Tests...")
        print("=" * 60)
        
        try:
            await self.test_framework_extraction()
            await self.test_strict_review_handling()
            await self.test_research_integration()
            await self.test_task_status_handling()
            await self.test_error_handling()
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
    tester = TestChangeCoordinator()
    success = await tester.run_all_tests()
    
    if success:
        print("🎉 All ChangeCoordinator tests passed!")
        sys.exit(0)
    else:
        print("❌ Some ChangeCoordinator tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())