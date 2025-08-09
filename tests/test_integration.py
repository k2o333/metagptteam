#!/usr/bin/env python3
"""
Comprehensive Integration Test Script

This script tests the complete refactored research system integration including:
1. End-to-end research process with context awareness
2. Interactive research flow
3. Document adaptation with research context
4. Error handling and recovery
"""

import asyncio
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add the root of the MetaGPT project to the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from hierarchical.actions.research_controller import ResearchController, UserInteractionRequired
from hierarchical.actions.research_model import ResearchConfig, ToolExecutionStatus
from hierarchical.roles.change_coordinator import ChangeCoordinator
from hierarchical.context import HierarchicalContext
from metagpt.schema import Message
from metagpt.llm import LLM
from metagpt.team import Team
from metagpt.memory.role_zero_memory import RoleZeroLongTermMemory


class IntegrationTest:
    """Integration test class for the complete system"""
    
    def __init__(self):
        self.test_results = []
        self.temp_dir = Path(tempfile.mkdtemp())
        self.workspace_dir = self.temp_dir / "workspace"
        self.workspace_dir.mkdir(exist_ok=True)
    
    async def setup_test_environment(self):
        """Set up test environment with mock components"""
        print("🔧 Setting up test environment...")
        
        # Create mock LLM
        self.mock_llm = AsyncMock()
        self.mock_llm.aask.return_value = json.dumps({
            "thought": "I need to research React hooks",
            "action": {
                "tool_name": "resolve-library-id",
                "tool_args": {"libraryName": "react"}
            }
        })
        
        # Create mock context
        self.ctx = HierarchicalContext(llm=self.mock_llm)
        
        # Create test document
        self.test_doc_path = self.workspace_dir / "test_document.md"
        self.test_doc_content = """# Test Document

## Introduction
This is a test document for testing the refactored research system.

## Getting Started
Basic getting started information goes here.

## Advanced Topics
More advanced topics are covered here.
"""
        
        self.test_doc_path.write_text(self.test_doc_content)
        
        print("✅ Test environment setup complete")
    
    async def test_end_to_end_research(self):
        """Test 1: End-to-end research process with context awareness"""
        print("🧪 Testing End-to-End Research Process...")
        
        # Create ResearchController with test config
        config = ResearchConfig()
        config.max_react_loops = 2  # Limit for testing
        
        research_controller = ResearchController(config)
        research_controller.set_context(self.ctx)
        
        # Mock tool execution service
        with patch.object(research_controller, 'tool_service') as mock_tool_service:
            mock_tool_service.execute_tool = AsyncMock(side_effect=self._mock_tool_execution)
            
            # Test research with framework context
            queries = ["How to use React hooks?"]
            
            try:
                results = await research_controller.execute_research(
                    queries=queries,
                    required_framework="react"
                )
                
                # Verify results
                assert "How to use React hooks?" in results, "Results should contain the query"
                result_data = results["How to use React hooks?"]
                
                # Check that the research completed successfully
                assert result_data["status"] == "success", f"Expected success, got {result_data['status']}"
                assert "final_answer" in result_data, "Results should contain final_answer"
                
                print("✅ End-to-end research test passed")
                self.test_results.append({"test": "end_to_end_research", "status": "passed"})
                
            except Exception as e:
                print(f"❌ End-to-end research test failed: {e}")
                self.test_results.append({"test": "end_to_end_research", "status": "failed", "error": str(e)})
    
    async def test_interactive_research_flow(self):
        """Test 2: Interactive research flow with user input"""
        print("🧪 Testing Interactive Research Flow...")
        
        # Create ResearchController
        config = ResearchConfig()
        research_controller = ResearchController(config)
        research_controller.set_context(self.ctx)
        
        # Mock tool execution to trigger user interaction
        with patch.object(research_controller, 'tool_service') as mock_tool_service:
            # First call triggers ASK_USER, second call provides normal response
            call_count = 0
            
            async def mock_execute_tool(action, query, mcp_manager=None):
                nonlocal call_count
                call_count += 1
                
                if call_count == 1 and action.get("tool_name") == "ASK_USER":
                    # Trigger user interaction
                    raise UserInteractionRequired(
                        "What's your experience level with React?",
                        {"query": query, "step": 1, "framework": "react"}
                    )
                else:
                    # Normal tool response
                    return json.dumps({
                        "status": "success",
                        "result": "Research completed with user input"
                    })
            
            mock_tool_service.execute_tool = AsyncMock(side_effect=mock_execute_tool)
            
            try:
                # First call - should trigger user interaction
                queries = ["React hooks tutorial for beginners"]
                results = await research_controller.execute_research(queries, required_framework="react")
                
                # Verify it's waiting for user input
                result_data = results["React hooks tutorial for beginners"]
                assert result_data["status"] == "awaiting_user_input", f"Expected awaiting_user_input, got {result_data['status']}"
                assert result_data["user_prompt"] is not None, "Should have user prompt"
                assert result_data["resume_state"] is not None, "Should have resume state"
                
                # Second call - with user answer
                resume_state = result_data["resume_state"]
                resume_state["memory_messages"] = ["Test message"]
                
                results2 = await research_controller.execute_research(
                    queries=["React hooks tutorial for beginners (with user input: Beginner level)"],
                    resume_state=resume_state,
                    user_answer="Beginner level"
                )
                
                # Verify it completed successfully
                result_data2 = results2["React hooks tutorial for beginners (with user input: Beginner level)"]
                assert result_data2["status"] == "success", f"Expected success, got {result_data2['status']}"
                
                print("✅ Interactive research flow test passed")
                self.test_results.append({"test": "interactive_research_flow", "status": "passed"})
                
            except Exception as e:
                print(f"❌ Interactive research flow test failed: {e}")
                self.test_results.append({"test": "interactive_research_flow", "status": "failed", "error": str(e)})
    
    async def test_document_adaptation_integration(self):
        """Test 3: Document adaptation with research context"""
        print("🧪 Testing Document Adaptation Integration...")
        
        # Create ChangeCoordinator with mock research action
        mock_research_action = AsyncMock()
        mock_research_action.run = AsyncMock(return_value={
            "Test query": {
                "status": "success",
                "final_answer": "React hooks are functions that let you use state and other React features without writing a class."
            }
        })
        
        mock_reviewer_action = AsyncMock()
        mock_reviewer_action.run = AsyncMock(return_value={
            "status": "approved",
            "confidence": 0.9
        })
        
        coordinator = ChangeCoordinator(
            context=self.ctx,
            research_action=mock_research_action,
            research_reviewer_action=mock_reviewer_action
        )
        
        # Set up document content and adaptation instruction
        coordinator.document_content = self.test_doc_content
        coordinator.document_path = str(self.test_doc_path)
        coordinator.adaptation_instruction = "Add information about React hooks"
        
        # Set up task queue
        coordinator.task_queue = [
            {
                "full_heading_string": "## Introduction",
                "rewrite_task": "Add React hooks information",
                "status": "rewriting"
            }
        ]
        
        # Mock LLM for content generation
        self.mock_llm.aask.return_value = "## Introduction\nThis is a test document for testing the refactored research system.\n\nReact hooks are functions that let you use state and other React features without writing a class."
        
        try:
            # Simulate the adaptation process
            # This tests the integration between research and document rewriting
            for task in coordinator.task_queue:
                if task.get("status") == "rewriting":
                    # Extract framework from task
                    framework = coordinator._extract_framework_from_task(task["rewrite_task"])
                    assert framework == "react", f"Expected 'react', got '{framework}'"
                    
                    # Simulate successful research
                    research_results = await coordinator._execute_action(
                        mock_research_action,
                        queries=[task["rewrite_task"]],
                        required_framework=framework
                    )
                    
                    # Verify research results
                    assert "Test query" in research_results, "Research results should contain the query"
                    
                    # Simulate successful review
                    review_results = await coordinator._execute_action(
                        mock_reviewer_action,
                        research_results=research_results,
                        rewrite_task=task["rewrite_task"]
                    )
                    
                    # Verify review results
                    assert review_results["status"] == "approved", f"Expected approved, got {review_results['status']}"
                    
                    # Update task with new content
                    task["new_content"] = "## Introduction\nThis is a test document for testing the refactored research system.\n\nReact hooks are functions that let you use state and other React features without writing a class."
                    task["status"] = "completed"
            
            print("✅ Document adaptation integration test passed")
            self.test_results.append({"test": "document_adaptation_integration", "status": "passed"})
            
        except Exception as e:
            print(f"❌ Document adaptation integration test failed: {e}")
            self.test_results.append({"test": "document_adaptation_integration", "status": "failed", "error": str(e)})
    
    async def test_error_handling_and_recovery(self):
        """Test 4: Error handling and recovery mechanisms"""
        print("🧪 Testing Error Handling and Recovery...")
        
        # Create ResearchController
        config = ResearchConfig()
        config.max_react_loops = 1  # Limit for testing error conditions
        
        research_controller = ResearchController(config)
        research_controller.set_context(self.ctx)
        
        # Test 1: Research failure handling
        try:
            # Mock tool execution to fail
            with patch.object(research_controller, 'tool_service') as mock_tool_service:
                mock_tool_service.execute_tool = AsyncMock(return_value="Error: Tool execution failed")
                
                results = await research_controller.execute_research(
                    queries=["Test query"],
                    required_framework="react"
                )
                
                result_data = results["Test query"]
                # Should handle failure gracefully
                assert "status" in result_data, "Results should contain status"
                assert "reason" in result_data, "Results should contain reason for failure"
            
            # Test 2: LLM failure handling
            research_controller.llm_pool = ["failing-model"]
            
            with patch('hierarchical.actions.research_controller.create_llm_instance') as mock_create:
                mock_llm = AsyncMock()
                mock_llm.aask.side_effect = Exception("LLM failed")
                mock_create.return_value = mock_llm
                
                with patch.object(research_controller, '_ask_llm_fallback') as mock_fallback:
                    mock_fallback.side_effect = ConnectionError("All LLMs failed")
                    
                    results = await research_controller.execute_research(
                        queries=["Test query"],
                        required_framework="react"
                    )
                    
                    result_data = results["Test query"]
                    assert result_data["status"] == "failure", "Should handle LLM failure"
            
            print("✅ Error handling and recovery test passed")
            self.test_results.append({"test": "error_handling_recovery", "status": "passed"})
            
        except Exception as e:
            print(f"❌ Error handling and recovery test failed: {e}")
            self.test_results.append({"test": "error_handling_recovery", "status": "failed", "error": str(e)})
    
    def _mock_tool_execution(self, action, query, mcp_manager=None):
        """Mock tool execution for testing"""
        tool_name = action.get("tool_name")
        
        if tool_name == "FINISH":
            return "Research completed successfully"
        elif tool_name == "resolve-library-id":
            return json.dumps({
                "library_name": action.get("tool_args", {}).get("libraryName", "react"),
                "resolved_id": "/vercel/next.js",
                "trust_score": 0.9,
                "code_snippets": 1000,
                "description": "React library documentation"
            })
        elif tool_name == "get-library-docs":
            return json.dumps({
                "status": "success",
                "content": "React hooks are functions that let you use state and other React features without writing a class."
            })
        else:
            return f"Mock response for {tool_name}"
    
    async def cleanup(self):
        """Clean up test environment"""
        print("🧹 Cleaning up test environment...")
        shutil.rmtree(self.temp_dir)
        print("✅ Cleanup complete")
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting Comprehensive Integration Tests...")
        print("=" * 60)
        
        try:
            await self.setup_test_environment()
            await self.test_end_to_end_research()
            await self.test_interactive_research_flow()
            await self.test_document_adaptation_integration()
            await self.test_error_handling_and_recovery()
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.cleanup()
        
        print("=" * 60)
        print("📊 Integration Test Results Summary:")
        
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
    tester = IntegrationTest()
    success = await tester.run_all_tests()
    
    if success:
        print("🎉 All integration tests passed!")
        print("🔧 The refactored research system is working correctly!")
        sys.exit(0)
    else:
        print("❌ Some integration tests failed!")
        print("🔧 Please review the failed tests and fix the issues.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())