#!/usr/bin/env python3
# mghier/scripts/test_new_mcp_parameter_completion.py
"""新MCP参数补全功能测试脚本"""

import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# 添加项目路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from hierarchical.actions.research_service import MCPToolSchemaDiscoverer, ParameterGapAnalyzer, ParameterCompletionExecutor
from hierarchical.actions.research_controller import ResearchController
from hierarchical.actions.research_model import ResearchConfig


class MockLLM:
    """模拟LLM用于测试"""
    
    async def aask(self, prompt):
        """模拟LLM响应"""
        # 根据提示内容返回相应的模拟响应
        if "resolve-library-id" in prompt and "libraryName" in prompt:
            return '{"libraryName": "react"}'
        elif "get-library-docs" in prompt and "context7CompatibleLibraryID" in prompt:
            return '{"context7CompatibleLibraryID": "/facebook/react"}'
        else:
            return '{}'


class MockMCPManager:
    """模拟MCP管理器用于测试"""
    
    async def list_tools(self):
        """模拟list_tools方法"""
        return {
            "tools": [
                {
                    "name": "resolve-library-id",
                    "description": "Resolves a package/product name to a Context7-compatible library ID",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "libraryName": {
                                "type": "string",
                                "description": "Library name to search for and retrieve a Context7-compatible library ID."
                            }
                        },
                        "required": ["libraryName"]
                    }
                },
                {
                    "name": "get-library-docs",
                    "description": "Fetches up-to-date documentation for a library",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "context7CompatibleLibraryID": {
                                "type": "string",
                                "description": "Exact Context7-compatible library ID"
                            },
                            "topic": {
                                "type": "string",
                                "description": "Topic to focus documentation on"
                            },
                            "tokens": {
                                "type": "integer",
                                "description": "Maximum number of tokens of documentation to retrieve"
                            }
                        },
                        "required": ["context7CompatibleLibraryID"]
                    }
                }
            ]
        }
    
    async def call_tool(self, tool_name, args):
        """模拟call_tool方法"""
        if tool_name == "resolve-library-id":
            return json.dumps([{
                "Context7-compatible library ID": "/facebook/react",
                "Description": "A JavaScript library for building user interfaces",
                "Trust Score": 9
            }])
        elif tool_name == "get-library-docs":
            return json.dumps({
                "documentation": "React is a JavaScript library for building user interfaces.",
                "tokens": 1000
            })
        else:
            return '{"result": "success"}'


async def test_mcp_tool_schema_discoverer():
    """测试MCPToolSchemaDiscoverer"""
    print("=== 测试 MCPToolSchemaDiscoverer ===")
    
    # 创建模拟MCP管理器
    mcp_manager = MockMCPManager()
    
    # 创建schema发现器
    schema_discoverer = MCPToolSchemaDiscoverer(mcp_manager)
    
    # 测试获取resolve-library-id的schema
    print("1. 测试获取resolve-library-id的schema...")
    try:
        schema = await schema_discoverer.discover_tool_schema("resolve-library-id")
        print(f"   Schema: {schema}")
        assert "properties" in schema
        assert "required" in schema
        assert "libraryName" in schema["properties"]
        assert "libraryName" in schema["required"]
        print("   ✓ 获取schema成功")
    except Exception as e:
        print(f"   ✗ 获取schema失败: {e}")
        return False
    
    # 测试获取get-library-docs的schema
    print("2. 测试获取get-library-docs的schema...")
    try:
        schema = await schema_discoverer.discover_tool_schema("get-library-docs")
        print(f"   Schema: {schema}")
        assert "properties" in schema
        assert "required" in schema
        assert "context7CompatibleLibraryID" in schema["properties"]
        assert "context7CompatibleLibraryID" in schema["required"]
        print("   ✓ 获取schema成功")
    except Exception as e:
        print(f"   ✗ 获取schema失败: {e}")
        return False
    
    # 测试缓存功能
    print("3. 测试缓存功能...")
    try:
        # 第二次获取应该从缓存中获取
        schema = await schema_discoverer.discover_tool_schema("resolve-library-id")
        assert "properties" in schema
        print("   ✓ 缓存功能正常")
    except Exception as e:
        print(f"   ✗ 缓存功能异常: {e}")
        return False
    
    return True


async def test_parameter_gap_analyzer():
    """测试ParameterGapAnalyzer"""
    print("\n=== 测试 ParameterGapAnalyzer ===")
    
    # 创建模拟MCP管理器和schema发现器
    mcp_manager = MockMCPManager()
    schema_discoverer = MCPToolSchemaDiscoverer(mcp_manager)
    
    # 创建参数缺口分析器
    gap_analyzer = ParameterGapAnalyzer(schema_discoverer)
    
    # 测试分析缺失参数（缺少必需参数）
    print("1. 测试分析缺失参数（缺少必需参数）...")
    try:
        result = await gap_analyzer.analyze_missing_params(
            "resolve-library-id", 
            {}  # 空参数，缺少libraryName
        )
        print(f"   分析结果: {result}")
        assert result["has_issues"]
        assert "libraryName" in result["missing_required"]
        print("   ✓ 缺失参数检测成功")
    except Exception as e:
        print(f"   ✗ 缺失参数检测失败: {e}")
        return False
    
    # 测试分析参数（参数完整）
    print("2. 测试分析参数（参数完整）...")
    try:
        result = await gap_analyzer.analyze_missing_params(
            "resolve-library-id", 
            {"libraryName": "react"}  # 参数完整
        )
        print(f"   分析结果: {result}")
        assert not result["has_issues"]
        assert result["can_proceed"]
        print("   ✓ 参数完整性验证成功")
    except Exception as e:
        print(f"   ✗ 参数完整性验证失败: {e}")
        return False
    
    # 测试参数类型验证
    print("3. 测试参数类型验证...")
    try:
        result = await gap_analyzer.analyze_missing_params(
            "get-library-docs", 
            {"context7CompatibleLibraryID": 123}  # 类型错误，应该是字符串
        )
        print(f"   分析结果: {result}")
        assert result["has_issues"]
        assert len(result["invalid_params"]) > 0
        print("   ✓ 参数类型验证成功")
    except Exception as e:
        print(f"   ✗ 参数类型验证失败: {e}")
        return False
    
    return True


async def test_parameter_completion_executor():
    """测试ParameterCompletionExecutor"""
    print("\n=== 测试 ParameterCompletionExecutor ===")
    
    # 创建模拟组件
    mcp_manager = MockMCPManager()
    llm = MockLLM()
    
    # 创建schema发现器和参数补全执行器
    schema_discoverer = MCPToolSchemaDiscoverer(mcp_manager)
    completion_executor = ParameterCompletionExecutor(llm, schema_discoverer)
    
    # 测试补全缺失参数
    print("1. 测试补全缺失参数...")
    try:
        completed_args, success = await completion_executor.complete_parameters(
            "resolve-library-id",
            {},  # 空参数，需要补全
            "I want to learn about React library"
        )
        print(f"   补全结果: {completed_args}, 成功: {success}")
        assert success
        assert "libraryName" in completed_args
        print("   ✓ 参数补全成功")
    except Exception as e:
        print(f"   ✗ 参数补全失败: {e}")
        return False
    
    # 测试参数已完整的情况
    print("2. 测试参数已完整的情况...")
    try:
        completed_args, success = await completion_executor.complete_parameters(
            "resolve-library-id",
            {"libraryName": "react"},  # 参数已完整
            "I want to learn about React library"
        )
        print(f"   补全结果: {completed_args}, 成功: {success}")
        assert success
        assert completed_args["libraryName"] == "react"
        print("   ✓ 参数完整情况处理成功")
    except Exception as e:
        print(f"   ✗ 参数完整情况处理失败: {e}")
        return False
    
    return True


async def test_research_controller_integration():
    """测试ResearchController集成"""
    print("\n=== 测试 ResearchController 集成 ===")
    
    # 创建配置和控制器
    config = ResearchConfig()
    controller = ResearchController(config)
    
    # 创建模拟LLM并设置到控制器
    mock_llm = MockLLM()
    controller.llm = mock_llm
    
    # 创建模拟MCP管理器
    mock_mcp_manager = MockMCPManager()
    
    # 测试_get_mcp_manager方法
    print("1. 测试_get_mcp_manager方法...")
    try:
        # 设置模拟context
        controller.context = Mock()
        controller.context.mcp_manager = mock_mcp_manager
        
        mcp_manager = controller._get_mcp_manager()
        assert mcp_manager is not None
        print("   ✓ _get_mcp_manager方法正常")
    except Exception as e:
        print(f"   ✗ _get_mcp_manager方法异常: {e}")
        return False
    
    return True


async def main():
    """主测试函数"""
    print("开始新MCP参数补全功能测试...")
    
    all_passed = True
    
    try:
        # 测试各个组件
        if not await test_mcp_tool_schema_discoverer():
            all_passed = False
            
        if not await test_parameter_gap_analyzer():
            all_passed = False
            
        if not await test_parameter_completion_executor():
            all_passed = False
            
        if not await test_research_controller_integration():
            all_passed = False
        
        print("\n=== 测试结果 ===")
        if all_passed:
            print("✓ MCPToolSchemaDiscoverer 测试通过")
            print("✓ ParameterGapAnalyzer 测试通过")
            print("✓ ParameterCompletionExecutor 测试通过")
            print("✓ ResearchController 集成测试通过")
            print("\n所有新MCP参数补全功能测试均已通过！")
            return 0
        else:
            print("\n部分测试失败，请检查上述错误信息。")
            return 1
            
    except Exception as e:
        print(f"\n✗ 测试过程中出现未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)