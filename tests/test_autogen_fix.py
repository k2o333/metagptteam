#!/usr/bin/env python3
"""Test script to verify the fixes for MCP parameter completion"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from hierarchical.actions.research_model import ResearchConfig
from hierarchical.actions.research_service import ToolExecutionService
from hierarchical.actions.parameter_manager import ParameterManager
from hierarchical.actions.result_processor import ResultProcessor
from hierarchical.actions.schema_registry import SchemaRegistry


async def test_autogen_resolution():
    """Test autogen library resolution"""
    print("=== Testing AutoGen Library Resolution ===")
    
    # Initialize components
    config = ResearchConfig()
    param_manager = ParameterManager(config)
    schema_registry = SchemaRegistry(config)
    result_processor = ResultProcessor(config)
    
    # Test 1: Check if autogen is in common library names
    print("1. Checking if 'autogen' is in common library names...")
    common_names = config.context7_config.common_library_names
    if "autogen" in common_names:
        print(f"   ✓ Found 'autogen' mapped to: {common_names['autogen']}")
    else:
        print("   ✗ 'autogen' not found in common library names")
        return False
    
    # Test 2: Test parameter validation
    print("2. Testing parameter validation for resolve-library-id...")
    schema = schema_registry.get_tool_schema("resolve-library-id")
    validation_result = param_manager.validate_parameters(
        "resolve-library-id", 
        {"libraryName": "autogen"}, 
        schema
    )
    if validation_result["valid"]:
        print("   ✓ Parameter validation passed")
    else:
        print(f"   ✗ Parameter validation failed: {validation_result['error']}")
        return False
    
    # Test 3: Test result formatting
    print("3. Testing result formatting...")
    test_result = {
        "resolved_id": "/microsoft/autogen",
        "library_name": "autogen",
        "description": "AutoGen Library",
        "trust_score": 9.5
    }
    
    formatted = result_processor.format_result_for_llm("resolve-library-id", test_result)
    print(f"   Formatted result: {formatted}")
    
    if "Resolved library ID: /microsoft/autogen" in formatted:
        print("   ✓ Result formatting works correctly")
    else:
        print("   ✗ Result formatting failed")
        return False
    
    # Test 4: Test quality validation
    print("4. Testing quality validation...")
    quality_result = result_processor.validate_result_quality(
        "resolve-library-id", test_result, "autogen framework documentation"
    )
    print(f"   Quality metrics: {quality_result}")
    
    # For resolve-library-id, the main thing is having a valid library ID
    if quality_result["is_valid"] and "No library ID found in result" not in str(quality_result["issues"]):
        print("   ✓ Quality validation passed (library ID found)")
    else:
        print("   ✗ Quality validation failed (library ID not found)")
        return False
    
    return True


async def main():
    """Main test function"""
    print("Starting MCP parameter completion fixes verification...\n")
    
    success = await test_autogen_resolution()
    
    if success:
        print("\n=== All Tests Passed ===")
        print("✓ AutoGen library resolution fixes verified successfully!")
        print("✓ The system should now be able to resolve 'autogen' library IDs")
        return 0
    else:
        print("\n=== Tests Failed ===")
        print("✗ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)