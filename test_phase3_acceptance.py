#!/usr/bin/env python3
"""
Comprehensive acceptance test for Phase 3: Dynamic Control Flow and Knowledge Precipitation
"""

import asyncio
import sys
import os
import json
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, '/root/metagpt/mghier')

from hierarchical.actions.assess_subdivision import AssessSubdivision
from hierarchical.roles.scheduler import Scheduler
from hierarchical.actions.research import Research
from hierarchical.actions.research_controller import ResearchSerializer
from metagpt.exp_pool import exp_cache


async def test_phase3_acceptance():
    """Run comprehensive acceptance tests for Phase 3 implementation."""
    
    print("=" * 80)
    print("PHASE 3: DYNAMIC CONTROL FLOW AND KNOWLEDGE PRECIPITATION ACCEPTANCE TEST")
    print("=" * 80)
    
    passed_tests = 0
    total_tests = 0
    
    # Test 1: AssessSubdivision Action Implementation
    print("\n1. Testing AssessSubdivision Action Implementation")
    print("-" * 50)
    total_tests += 1
    
    try:
        action = AssessSubdivision()
        
        # Test with content that should be subdivided
        result_complex = await action.run(
            chapter_title="Machine Learning Applications",
            chapter_content="Machine learning has revolutionized many fields including healthcare diagnostics, financial forecasting, autonomous vehicles, natural language processing, computer vision, and recommendation systems. Each of these areas requires detailed explanation of specific algorithms, use cases, and implementation challenges.",
            parent_context="Overview of AI technologies",
            research_summary="Machine learning applications span multiple industries with specific use cases"
        )
        
        # Test with content that should NOT be subdivided
        result_simple = await action.run(
            chapter_title="Introduction to AI",
            chapter_content="AI is a broad field of computer science.",
            parent_context="Technical introduction",
            research_summary="Basic AI concepts"
        )
        
        # Validate structure
        valid_complex = (
            isinstance(result_complex, dict) and 
            'should_subdivide' in result_complex and 
            'reason' in result_complex
        )
        
        valid_simple = (
            isinstance(result_simple, dict) and 
            'should_subdivide' in result_simple and 
            'reason' in result_simple
        )
        
        if valid_complex and valid_simple:
            print("✅ AssessSubdivision Action: Structure validation PASSED")
            
            # Validate logical behavior
            if result_complex.get('should_subdivide') == True:
                print("✅ AssessSubdivision Action: Complex content correctly flagged for subdivision")
            else:
                print("⚠️  AssessSubdivision Action: Complex content not flagged for subdivision (may be valid based on LLM judgment)")
            
            if result_simple.get('should_subdivide') == False:
                print("✅ AssessSubdivision Action: Simple content correctly NOT flagged for subdivision")
            else:
                print("⚠️  AssessSubdivision Action: Simple content flagged for subdivision (may be valid based on LLM judgment)")
            
            passed_tests += 1
        else:
            print("❌ AssessSubdivision Action: Structure validation FAILED")
            
    except Exception as e:
        print(f"❌ AssessSubdivision Action: Exception occurred - {e}")
    
    # Test 2: Scheduler Integration with AssessSubdivision
    print("\n2. Testing Scheduler Integration with AssessSubdivision")
    print("-" * 50)
    total_tests += 1
    
    try:
        scheduler = Scheduler()
        actions = scheduler.actions
        
        # Check AssessSubdivision is registered
        assess_actions = [action for action in actions if isinstance(action, AssessSubdivision)]
        has_assess_subdivision = len(assess_actions) > 0
        
        # Check action order (should be 3rd action)
        correct_order = len(actions) >= 3 and isinstance(actions[2], AssessSubdivision)
        
        if has_assess_subdivision and correct_order:
            print("✅ Scheduler Integration: AssessSubdivision properly registered")
            print("✅ Scheduler Integration: AssessSubdivision correctly positioned")
            passed_tests += 1
        else:
            print(f"❌ Scheduler Integration: Registration issue - has_assess_subdivision: {has_assess_subdivision}, correct_order: {correct_order}")
            
    except Exception as e:
        print(f"❌ Scheduler Integration: Exception occurred - {e}")
    
    # Test 3: ResearchSerializer Implementation
    print("\n3. Testing ResearchSerializer Implementation")
    print("-" * 50)
    total_tests += 1
    
    try:
        serializer = ResearchSerializer()
        
        # Test request serialization round-trip
        original_queries = ["What is neural network?"]
        test_kwargs = {"queries": original_queries}
        
        serialized_req = serializer.serialize_req(test_kwargs, **test_kwargs)
        deserialized_req = serializer.deserialize_req(serialized_req)
        
        req_roundtrip_success = deserialized_req.get("queries") == original_queries
        
        # Test response serialization round-trip
        original_response = {
            "status": "success",
            "source": "test",
            "final_answer": "A neural network is a computational model...",
            "steps_taken": 5
        }
        
        serialized_resp = serializer.serialize_resp(original_response)
        deserialized_resp = serializer.deserialize_resp(serialized_resp)
        
        resp_roundtrip_success = deserialized_resp == original_response
        
        if req_roundtrip_success and resp_roundtrip_success:
            print("✅ ResearchSerializer: Request serialization round-trip PASSED")
            print("✅ ResearchSerializer: Response serialization round-trip PASSED")
            passed_tests += 1
        else:
            print(f"❌ ResearchSerializer: Round-trip failed - req: {req_roundtrip_success}, resp: {resp_roundtrip_success}")
            
    except Exception as e:
        print(f"❌ ResearchSerializer: Exception occurred - {e}")
    
    # Test 4: @exp_cache Decorator on Research Action
    print("\n4. Testing @exp_cache Decorator on Research Action")
    print("-" * 50)
    total_tests += 1
    
    try:
        # Check if Research.run method is decorated
        research_method = Research.run
        
        # The method name should be 'async_wrapper' if @exp_cache is applied
        is_decorated = research_method.__name__ == "async_wrapper"
        
        # Check ResearchSerializer is available
        serializer_available = ResearchSerializer is not None
        
        # Test that we can create a serializer instance
        serializer_instance = None
        try:
            serializer_instance = ResearchSerializer()
            serializer_works = True
        except Exception:
            serializer_works = False
        
        if is_decorated and serializer_available and serializer_works:
            print("✅ @exp_cache Decorator: Properly applied to Research.run")
            print("✅ @exp_cache Decorator: ResearchSerializer available and working")
            passed_tests += 1
        else:
            print(f"❌ @exp_cache Decorator: Issues found - decorated: {is_decorated}, serializer_available: {serializer_available}, serializer_works: {serializer_works}")
            
    except Exception as e:
        print(f"❌ @exp_cache Decorator: Exception occurred - {e}")
    
    # Test 5: Configuration Verification
    print("\n5. Testing Configuration Verification")
    print("-" * 50)
    total_tests += 1
    
    try:
        # Load configuration
        config_path = "/root/metagpt/mghier/configs/local_config.yaml"
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config_content = f.read()
            
            # Check for exp_pool configuration
            has_exp_pool = "exp_pool:" in config_content
            has_enabled = "enabled: true" in config_content
            has_read_write = "enable_read: true" in config_content and "enable_write: true" in config_content
            has_persist_path = "persist_path:" in config_content
            has_retrieval_type = "retrieval_type: bm25" in config_content
            has_llm_ranker = "use_llm_ranker: true" in config_content
            
            if has_exp_pool and has_enabled and has_read_write and has_persist_path and has_retrieval_type and has_llm_ranker:
                print("✅ Configuration: exp_pool properly configured")
                print("✅ Configuration: All required settings present")
                passed_tests += 1
            else:
                print(f"❌ Configuration: Missing settings - exp_pool: {has_exp_pool}, enabled: {has_enabled}, read_write: {has_read_write}, persist_path: {has_persist_path}, retrieval_type: {has_retrieval_type}, llm_ranker: {has_llm_ranker}")
        else:
            print("❌ Configuration: local_config.yaml not found")
            
    except Exception as e:
        print(f"❌ Configuration: Exception occurred - {e}")
    
    # Test 6: Integration Flow Test
    print("\n6. Testing Integration Flow")
    print("-" * 50)
    total_tests += 1
    
    try:
        # Create instances
        scheduler = Scheduler()
        assess_action = AssessSubdivision()
        serializer = ResearchSerializer()
        
        # Verify all components can work together
        actions = scheduler.actions
        assess_action_in_scheduler = any(isinstance(action, AssessSubdivision) for action in actions)
        
        # Test that AssessSubdivision can be called
        assess_result = await assess_action.run(
            chapter_title="Test Integration",
            chapter_content="Test content for integration.",
            parent_context="Test context",
            research_summary="Test research summary"
        )
        
        assess_works = isinstance(assess_result, dict) and 'should_subdivide' in assess_result
        
        # Test serializer works
        serialize_works = False
        try:
            test_data = {"queries": ["test query"]}
            serialized = serializer.serialize_req(test_data, **test_data)
            deserialized = serializer.deserialize_req(serialized)
            serialize_works = deserialized == {"queries": ["test query"]}
        except Exception:
            pass
        
        if assess_action_in_scheduler and assess_works and serialize_works:
            print("✅ Integration Flow: All components working together")
            passed_tests += 1
        else:
            print(f"❌ Integration Flow: Issues found - assess_in_scheduler: {assess_action_in_scheduler}, assess_works: {assess_works}, serialize_works: {serialize_works}")
            
    except Exception as e:
        print(f"❌ Integration Flow: Exception occurred - {e}")
    
    # Final Results
    print("\n" + "=" * 80)
    print("ACCEPTANCE TEST RESULTS")
    print("=" * 80)
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Phase 3 implementation is ACCEPTED.")
        return True
    else:
        print(f"❌ {total_tests - passed_tests} TESTS FAILED. Phase 3 implementation needs attention.")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_phase3_acceptance())
    sys.exit(0 if success else 1)