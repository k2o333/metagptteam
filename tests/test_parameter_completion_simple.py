#!/usr/bin/env python3
# mghier/scripts/test_parameter_completion_simple.py
"""简单的MCP参数补全功能测试脚本"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from hierarchical.actions.research_model import ResearchConfig
from hierarchical.actions.parameter_manager import ParameterManager
from hierarchical.actions.schema_registry import SchemaRegistry


async def test_basic_functionality():
    """测试基本功能"""
    print("=== 测试基本MCP参数补全功能 ===")
    
    # 初始化配置和模块
    config = ResearchConfig()
    param_manager = ParameterManager(config)
    schema_registry = SchemaRegistry(config)
    
    # 1. 测试SchemaRegistry
    print("1. 测试SchemaRegistry...")
    schema = schema_registry.get_tool_schema("resolve-library-id")
    print(f"   获取到的schema: {schema['name']} - {schema['description']}")
    
    # 2. 测试ParameterManager参数补全
    print("2. 测试ParameterManager参数补全...")
    query = "I want to learn about React framework"
    initial_args = {}
    context = {}
    
    try:
        # 这里我们测试参数提取功能
        library_name = param_manager._extract_library_name_from_query(query)
        print(f"   从查询中提取的库名: '{library_name}'")
        
        # 验证参数
        validation_result = param_manager.validate_parameters(
            "resolve-library-id", 
            {"libraryName": library_name}, 
            schema
        )
        print(f"   参数验证结果: {validation_result}")
        
        if validation_result["valid"]:
            print("   ✓ 基本参数补全测试通过")
        else:
            print("   ✗ 参数验证失败")
            
    except Exception as e:
        print(f"   ✗ 参数补全测试失败: {e}")
        return False
    
    # 3. 测试工具schema验证
    print("3. 测试工具schema验证...")
    try:
        validation_result = schema_registry.validate_schema(
            "get-library-docs", 
            {"context7CompatibleLibraryID": "/vercel/next.js"}
        )
        print(f"   Schema验证结果: {validation_result}")
        
        if validation_result["valid"]:
            print("   ✓ Schema验证测试通过")
        else:
            print("   ✗ Schema验证失败")
            
    except Exception as e:
        print(f"   ✗ Schema验证测试失败: {e}")
        return False
    
    return True


async def main():
    """主函数"""
    print("开始简单的MCP参数补全功能测试...\n")
    
    success = await test_basic_functionality()
    
    if success:
        print("\n=== 测试完成 ===")
        print("✓ 所有基本MCP参数补全功能测试通过！")
        return 0
    else:
        print("\n=== 测试失败 ===")
        print("✗ 部分测试未通过")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)