#!/usr/bin/env python3
"""
Test script to verify the ReAct cycle fallback mechanism when LLM is unavailable.
This script simulates the scenario where LLM connection fails and tests the fallback behavior.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from hierarchical.actions.research_controller import ResearchController
from hierarchical.actions.research_model import ResearchConfig, ToolExecutionStatus


async def test_react_cycle_fallback():
    """Test ReAct cycle fallback when LLM is unavailable"""
    print("Testing ReAct cycle fallback mechanism...")
    
    # Create a research controller with minimal config
    config = ResearchConfig()
    controller = ResearchController(config)
    
    # Test query
    test_query = "What is MetaGPT?"
    
    try:
        # This should trigger the fallback mechanism since no LLM is configured
        result = await controller.execute_research([test_query])
        
        # Check the result
        if test_query in result:
            research_result = result[test_query]
            
            print(f"Query: {research_result.get('query', 'N/A')}")
            print(f"Status: {research_result.get('status', 'N/A')}")
            print(f"Final Answer: {research_result.get('final_answer', 'N/A')}")
            print(f"Reason: {research_result.get('reason', 'N/A')}")
            print(f"Source: {research_result.get('source', 'N/A')}")
            
            # Verify fallback behavior
            if research_result.get('status') == ToolExecutionStatus.FAILURE.value:
                if "LLM unavailable" in research_result.get('reason', ''):
                    print("✅ PASS: Fallback mechanism worked correctly")
                    return True
                else:
                    print("❌ FAIL: Fallback triggered but wrong reason")
                    return False
            else:
                print(f"❌ FAIL: Expected FAILURE status but got {research_result.get('status')}")
                return False
        else:
            print("❌ FAIL: No result returned for test query")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Unexpected exception: {e}")
        return False


async def test_llm_availability_check():
    """Test the _ask_llm method directly"""
    print("\nTesting _ask_llm method...")
    
    config = ResearchConfig()
    controller = ResearchController(config)
    
    try:
        # This should raise ConnectionError
        result = await controller._ask_llm("Test prompt")
        print(f"❌ FAIL: Expected ConnectionError but got result: {result}")
        return False
    except ConnectionError as e:
        if "No LLM available for ReAct cycle" in str(e):
            print("✅ PASS: _ask_llm correctly raised ConnectionError")
            return True
        else:
            print(f"❌ FAIL: Wrong error message: {e}")
            return False
    except Exception as e:
        print(f"❌ FAIL: Unexpected exception: {e}")
        return False


async def main():
    """Main test function"""
    print("=" * 50)
    print("Testing ReAct Cycle Fallback Mechanism")
    print("=" * 50)
    
    tests = [
        ("LLM Availability Check", test_llm_availability_check),
        ("ReAct Cycle Fallback", test_react_cycle_fallback),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if await test_func():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All tests passed! Fallback mechanism is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)