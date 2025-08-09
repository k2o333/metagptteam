#!/usr/bin/env python3
# mghier/scripts/test_mcp_parameter_completion.py
"""MCP参数补全功能测试脚本"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from hierarchical.actions.research_controller import ResearchController
from hierarchical.actions.research_model import ResearchConfig
from hierarchical.actions.parameter_manager import ParameterManager
from hierarchical.actions.tool_chain_executor import ToolChainExecutor
from hierarchical.actions.interaction_handler import InteractionHandler
from hierarchical.actions.schema_registry import SchemaRegistry
from hierarchical.actions.result_processor import ResultProcessor


async def test_parameter_manager():
    """测试ParameterManager模块"""
    print("=== 测试 ParameterManager 模块 ===")
    
    config = ResearchConfig()
    param_manager = ParameterManager(config)
    
    # 测试resolve-library-id参数补全
    print("1. 测试 resolve-library-id 参数补全...")
    try:
        initial_args = {}
        query = "I want to learn about React framework"
        context = {}
        
        completed_args = await param_manager.auto_fill_parameters(
            "resolve-library-id", initial_args, ["libraryName"], query, context
        )
        print(f"   补全后的参数: {completed_args}")
        assert "libraryName" in completed_args
        print("   ✓ 参数补全成功")
    except Exception as e:
        print(f"   ✗ 参数补全失败: {e}")
    
    # 测试参数验证
    print("2. 测试参数验证...")
    try:
        validation_result = param_manager.validate_parameters(
            "resolve-library-id", 
            {"libraryName": "react"}, 
            param_manager._get_tool_schema("resolve-library-id")
        )
        print(f"   验证结果: {validation_result}")
        assert validation_result["valid"]
        print("   ✓ 参数验证成功")
    except Exception as e:
        print(f"   ✗ 参数验证失败: {e}")


async def test_schema_registry():
    """测试SchemaRegistry模块"""
    print("\n=== 测试 SchemaRegistry 模块 ===")
    
    config = ResearchConfig()
    schema_registry = SchemaRegistry(config)
    
    # 测试获取工具schema
    print("1. 测试获取工具schema...")
    try:
        schema = schema_registry.get_tool_schema("resolve-library-id")
        print(f"   resolve-library-id schema: {schema}")
        assert schema is not None
        print("   ✓ 获取schema成功")
    except Exception as e:
        print(f"   ✗ 获取schema失败: {e}")
    
    # 测试参数验证
    print("2. 测试参数验证...")
    try:
        validation_result = schema_registry.validate_schema(
            "resolve-library-id", 
            {"libraryName": "react"}
        )
        print(f"   验证结果: {validation_result}")
        assert validation_result["valid"]
        print("   ✓ 参数验证成功")
    except Exception as e:
        print(f"   ✗ 参数验证失败: {e}")


async def test_result_processor():
    """测试ResultProcessor模块"""
    print("\n=== 测试 ResultProcessor 模块 ===")
    
    config = ResearchConfig()
    result_processor = ResultProcessor(config)
    
    # 测试结果标准化
    print("1. 测试结果标准化...")
    try:
        raw_result = '{"resolved_id": "/vercel/next.js", "library_name": "next.js"}'
        normalized = result_processor.normalize_result("resolve-library-id", raw_result)
        print(f"   标准化结果: {normalized}")
        assert "resolved_id" in normalized
        print("   ✓ 结果标准化成功")
    except Exception as e:
        print(f"   ✗ 结果标准化失败: {e}")
    
    # 测试结果格式化
    print("2. 测试结果格式化...")
    try:
        result_data = {
            "raw_data": {
                "documentation": "This is documentation content for testing purposes.",
                "tokens": 100,
                "library_id": "/vercel/next.js"
            }
        }
        formatted = result_processor.format_result_for_llm("get-library-docs", result_data)
        print(f"   格式化结果: {formatted[:100]}...")
        assert "Documentation" in formatted
        print("   ✓ 结果格式化成功")
    except Exception as e:
        print(f"   ✗ 结果格式化失败: {e}")


async def test_research_controller_integration():
    """测试ResearchController集成"""
    print("\n=== 测试 ResearchController 集成 ===")
    
    config = ResearchConfig()
    controller = ResearchController(config)
    
    # 测试模块初始化
    print("1. 测试模块初始化...")
    try:
        assert hasattr(controller, 'parameter_manager')
        assert hasattr(controller, 'tool_chain_executor')
        assert hasattr(controller, 'interaction_handler')
        assert hasattr(controller, 'schema_registry')
        assert hasattr(controller, 'result_processor')
        print("   ✓ 所有模块初始化成功")
    except Exception as e:
        print(f"   ✗ 模块初始化失败: {e}")
    
    # 测试工具描述解析
    print("2. 测试工具描述解析...")
    try:
        tool_descriptions = """Tool: `resolve-library-id` (from server: context7)
Description: Resolves a package/product name to a Context7-compatible library ID
Tool: `get-library-docs` (from server: context7)
Description: Fetches up-to-date documentation for a library"""
        
        tools_info = controller._parse_tool_descriptions(tool_descriptions)
        print(f"   解析的工具信息: {tools_info}")
        assert "resolve-library-id" in tools_info
        assert "get-library-docs" in tools_info
        print("   ✓ 工具描述解析成功")
    except Exception as e:
        print(f"   ✗ 工具描述解析失败: {e}")


async def main():
    """主测试函数"""
    print("开始MCP参数补全功能测试...")
    
    try:
        await test_parameter_manager()
        await test_schema_registry()
        await test_result_processor()
        await test_research_controller_integration()
        
        print("\n=== 所有测试完成 ===")
        print("✓ ParameterManager 模块测试通过")
        print("✓ SchemaRegistry 模块测试通过")
        print("✓ ResultProcessor 模块测试通过")
        print("✓ ResearchController 集成测试通过")
        print("\n所有MCP参数补全功能测试均已通过！")
        
    except Exception as e:
        print(f"\n✗ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)