#!/usr/bin/env python3
"""
Comprehensive acceptance test for Stage 4: Advanced Document Adaptation Workflow
"""

import asyncio
import sys
import os
import json
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, '/root/metagpt/mghier')

from hierarchical.actions.analyze_changes import AnalyzeChanges
from hierarchical.roles.change_coordinator import ChangeCoordinator
from hierarchical.roles.change_applier import ChangeApplier
from hierarchical.actions.rewrite_section import RewriteSection


async def test_stage4_acceptance():
    """Run comprehensive acceptance tests for Stage 4 implementation."""
    
    print("=" * 80)
    print("STAGE 4: ADVANCED DOCUMENT ADAPTATION WORKFLOW ACCEPTANCE TEST")
    print("=" * 80)
    
    passed_tests = 0
    total_tests = 0
    
    # Test 1: AnalyzeChanges Action Implementation
    print("\n1. Testing AnalyzeChanges Action Implementation")
    print("-" * 50)
    total_tests += 1
    
    try:
        action = AnalyzeChanges()
        
        # Test document content
        test_document = """# Simple Test Document

This is a simple test document.

## Introduction

This is the introduction section.

## Main Content

This is the main content section.

## Conclusion

This is the conclusion section."""
        
        # Test adaptation instruction
        adaptation_instruction = "Change 'This is a simple test document.' to 'This is a formal test document.' Also change 'This is the introduction section.' to 'This section provides an overview of the document.'"
        
        # Run the action
        result = await action.run(
            document_content=test_document,
            adaptation_instruction=adaptation_instruction
        )
        
        # Validate structure
        if isinstance(result, list) and len(result) >= 1:
            first_change = result[0]
            has_required_fields = (
                'start_line' in first_change and
                'start_char' in first_change and
                'end_line' in first_change and
                'end_char' in first_change and
                'rewrite_task' in first_change
            )
            
            if has_required_fields:
                print("✅ AnalyzeChanges Action: Structure validation PASSED")
                print("✅ AnalyzeChanges Action: Returns correct field structure")
                passed_tests += 1
            else:
                print("❌ AnalyzeChanges Action: Missing required fields")
        else:
            print("❌ AnalyzeChanges Action: Incorrect return type or empty result")
            
    except Exception as e:
        print(f"❌ AnalyzeChanges Action: Exception occurred - {e}")
    
    # Test 2: ChangeCoordinator Role Implementation
    print("\n2. Testing ChangeCoordinator Role Implementation")
    print("-" * 50)
    total_tests += 1
    
    try:
        coordinator = ChangeCoordinator()
        
        # Check that the role has the required attributes
        has_name = hasattr(coordinator, 'name') and coordinator.name == "ChangeCoordinator"
        has_profile = hasattr(coordinator, 'profile') and coordinator.profile == "Document Change Coordinator"
        has_goal = hasattr(coordinator, 'goal') and "document adaptation" in coordinator.goal.lower()
        
        # Check that it has the AnalyzeChanges action
        has_analyze_action = any(isinstance(action, AnalyzeChanges) for action in coordinator.actions)
        
        if has_name and has_profile and has_goal and has_analyze_action:
            print("✅ ChangeCoordinator Role: Basic attributes validated")
            print("✅ ChangeCoordinator Role: AnalyzeChanges action registered")
            passed_tests += 1
        else:
            print(f"❌ ChangeCoordinator Role: Issues found - name: {has_name}, profile: {has_profile}, goal: {has_goal}, analyze_action: {has_analyze_action}")
            
    except Exception as e:
        print(f"❌ ChangeCoordinator Role: Exception occurred - {e}")
    
    # Test 3: ChangeApplier Role Implementation
    print("\n3. Testing ChangeApplier Role Implementation")
    print("-" * 50)
    total_tests += 1
    
    try:
        applier = ChangeApplier()
        
        # Check that the role has the required attributes
        has_name = hasattr(applier, 'name') and applier.name == "ChangeApplier"
        has_profile = hasattr(applier, 'profile') and applier.profile == "Change Applier"
        has_goal = hasattr(applier, 'goal') and "apply text changes" in applier.goal.lower()
        
        if has_name and has_profile and has_goal:
            print("✅ ChangeApplier Role: Basic attributes validated")
            passed_tests += 1
        else:
            print(f"❌ ChangeApplier Role: Issues found - name: {has_name}, profile: {has_profile}, goal: {has_goal}")
            
    except Exception as e:
        print(f"❌ ChangeApplier Role: Exception occurred - {e}")
    
    # Test 4: RewriteSection Action Implementation
    print("\n4. Testing RewriteSection Action Implementation")
    print("-" * 50)
    total_tests += 1
    
    try:
        action = RewriteSection()
        
        # Check that the action has the required attributes
        has_name = hasattr(action, 'name') and "Rewrite" in action.name
        
        # Test basic functionality
        result = await action.run(
            original_text="This is a simple test document.",
            rewrite_instruction="Change 'This is a simple test document.' to 'This is a formal test document.'",
            full_document="# Test Document\n\nThis is a simple test document.\n"
        )
        
        if has_name and isinstance(result, str) and len(result) > 0:
            print("✅ RewriteSection Action: Basic attributes validated")
            print("✅ RewriteSection Action: Returns non-empty string result")
            passed_tests += 1
        else:
            print(f"❌ RewriteSection Action: Issues found - name: {has_name}, result_type: {type(result)}, result_length: {len(result) if result else 0}")
            
    except Exception as e:
        print(f"❌ RewriteSection Action: Exception occurred - {e}")
    
    # Test 5: Integration Test with Actual Document Processing
    print("\n5. Testing Integration with Actual Document Processing")
    print("-" * 50)
    total_tests += 1
    
    try:
        # Create a temporary test document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# Simple Test Document

This is a simple test document.

## Introduction

This is the introduction section.

## Main Content

This is the main content section.

## Conclusion

This is the conclusion section.""")
            test_doc_path = f.name
        
        try:
            # Test the _apply_text_change method directly
            applier = ChangeApplier()
            
            with open(test_doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply a simple change
            modified_content = applier._apply_text_change(
                content,
                "This is a formal test document.",
                {
                    "start_line": 2,
                    "start_char": 0,
                    "end_line": 2,
                    "end_char": 31
                }
            )
            
            # Check that the change was applied
            if "This is a formal test document." in modified_content:
                print("✅ Integration Test: Text replacement working correctly")
                passed_tests += 1
            else:
                print("❌ Integration Test: Text replacement failed")
                
        finally:
            # Clean up
            os.unlink(test_doc_path)
            
    except Exception as e:
        print(f"❌ Integration Test: Exception occurred - {e}")
    
    # Test 6: Complete Workflow Test
    print("\n6. Testing Complete Workflow Components")
    print("-" * 50)
    total_tests += 1
    
    try:
        # Check that all required files exist
        required_files = [
            "/root/metagpt/mghier/scripts/adapt_document.py",
            "/root/metagpt/mghier/scripts/test_adapt_document.py",
            "/root/metagpt/mghier/hierarchical/actions/analyze_changes.py",
            "/root/metagpt/mghier/hierarchical/actions/rewrite_section.py",
            "/root/metagpt/mghier/hierarchical/roles/change_coordinator.py",
            "/root/metagpt/mghier/hierarchical/roles/change_applier.py"
        ]
        
        all_files_exist = all(os.path.exists(f) for f in required_files)
        
        if all_files_exist:
            print("✅ Complete Workflow: All required files present")
            passed_tests += 1
        else:
            missing_files = [f for f in required_files if not os.path.exists(f)]
            print(f"❌ Complete Workflow: Missing files - {missing_files}")
            
    except Exception as e:
        print(f"❌ Complete Workflow: Exception occurred - {e}")
    
    # Final Results
    print("\n" + "=" * 80)
    print("ACCEPTANCE TEST RESULTS")
    print("=" * 80)
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Stage 4 implementation is ACCEPTED.")
        return True
    else:
        print(f"❌ {total_tests - passed_tests} TESTS FAILED. Stage 4 implementation needs attention.")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_stage4_acceptance())
    sys.exit(0 if success else 1)