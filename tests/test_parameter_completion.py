#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试ResearchController中LLM访问的完整修复
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from hierarchical.actions.research_controller import ResearchController, ResearchConfig
from hierarchical.actions.research_service import ParameterCompletionExecutor, MCPToolSchemaDiscoverer


async def test_parameter_completion_executor():
    """测试ParameterCompletionExecutor是否能正确访问LLM"""
    print("Testing ParameterCompletionExecutor LLM access...")
    
    # 创建配置
    config = ResearchConfig()
    
    # 创建ResearchController实例（不传入LLM，测试备用方案）
    controller = ResearchController(config=config, llm=None)
    print(f"ResearchController created with LLM: {controller.llm is not None}")
    
    # 测试_get_llm_fallback方法
    fallback_llm = controller._get_llm_fallback()
    print(f"Fallback LLM available: {fallback_llm is not None}")
    
    # 测试ParameterCompletionExecutor的初始化
    # 创建一个模拟的mcp_manager
    class MockMCPManager:
        async def list_tools(self):
            return {
                "tools": [
                    {
                        "name": "resolve-library-id",
                        "inputSchema": {
                            "properties": {
                                "libraryName": {"type": "string", "description": "Library name to resolve"}
                            },
                            "required": ["libraryName"],
                            "type": "object"
                        }
                    }
                ]
            }
    
    mcp_manager = MockMCPManager()
    schema_discoverer = MCPToolSchemaDiscoverer(mcp_manager)
    
    # 测试使用Controller自身的LLM（应该为None）
    llm_to_use = controller.llm or controller._get_llm_fallback()
    print(f"LLM to use for ParameterCompletionExecutor: {llm_to_use is not None}")
    
    # 创建ParameterCompletionExecutor实例
    completion_executor = ParameterCompletionExecutor(llm_to_use, schema_discoverer)
    print(f"ParameterCompletionExecutor created with LLM: {completion_executor.llm is not None}")
    
    print("Test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_parameter_completion_executor())