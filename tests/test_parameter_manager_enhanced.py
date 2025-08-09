#!/usr/bin/env python3
"""
测试增强版参数管理功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT.parent))

from hierarchical.actions.parameter_manager import ParameterManager, ParameterPattern
from hierarchical.actions.research_model import ResearchConfig

async def test_parameter_manager_enhanced():
    """测试增强版参数管理器"""
    print("🧪 测试增强版参数管理器...")
    
    # 创建参数管理器实例
    config = ResearchConfig()
    # 启用学习型参数补全策略
    config.parameter_completion = {
        "enabled": True,
        "max_interaction_rounds": 3,
        "timeout_seconds": 60,
        "strategies": {
            "schema_based": {"enabled": True, "priority": 1},
            "context_aware": {"enabled": True, "priority": 2},
            "historical_based": {"enabled": True, "priority": 3},
            "learning_based": {"enabled": True, "priority": 4},  # 启用学习型策略
            "user_interaction": {"enabled": True, "priority": 5}
        }
    }
    
    parameter_manager = ParameterManager(config)
    
    print("\n" + "="*60)
    print("测试1: 基于学习的参数补全")
    print("="*60)
    
    # 创建一些历史参数模式用于学习
    pattern1 = ParameterPattern(
        tool_name="resolve-library-id",
        parameters={"libraryName": "react"},
        context={"query": "how to use react hooks"},
        success=True,
        frequency=5
    )
    
    pattern2 = ParameterPattern(
        tool_name="get-library-docs",
        parameters={
            "context7CompatibleLibraryID": "/vercel/next.js",
            "topic": "hooks"
        },
        context={"query": "react hooks documentation"},
        success=True,
        frequency=3
    )
    
    pattern3 = ParameterPattern(
        tool_name="resolve-library-id",
        parameters={"libraryName": "django"},
        context={"query": "django models tutorial"},
        success=True,
        frequency=4
    )
    
    # 存储模式
    parameter_manager.parameter_patterns["resolve-library-id:how to use react hooks"] = [pattern1]
    parameter_manager.parameter_patterns["get-library-docs:react hooks documentation"] = [pattern2]
    parameter_manager.parameter_patterns["resolve-library-id:django models tutorial"] = [pattern3]
    
    # 测试基于学习的参数补全
    tool_name1 = "resolve-library-id"
    initial_args1 = {}
    query1 = "how to use react hooks"
    context1 = {"query": query1, "user_id": "user_123"}
    
    completed_args1 = await parameter_manager.complete_parameters(
        tool_name1, initial_args1, query1, context1
    )
    
    print(f"工具: {tool_name1}")
    print(f"初始参数: {initial_args1}")
    print(f"查询: {query1}")
    print(f"补全后参数: {completed_args1}")
    
    print("\n" + "-"*40)
    
    tool_name2 = "get-library-docs"
    initial_args2 = {"context7CompatibleLibraryID": "/vercel/next.js"}
    query2 = "react hooks documentation"
    context2 = {"query": query2, "user_id": "user_123"}
    
    completed_args2 = await parameter_manager.complete_parameters(
        tool_name2, initial_args2, query2, context2
    )
    
    print(f"工具: {tool_name2}")
    print(f"初始参数: {initial_args2}")
    print(f"查询: {query2}")
    print(f"补全后参数: {completed_args2}")
    
    print("\n" + "="*60)
    print("测试2: 用户习惯学习")
    print("="*60)
    
    # 更新用户习惯
    parameter_manager.update_parameter_patterns(
        "resolve-library-id",
        {"libraryName": "vue"},
        {"query": "vue component lifecycle", "user_id": "user_456"},
        success=True
    )
    
    # 测试用户习惯适配
    tool_name3 = "resolve-library-id"
    initial_args3 = {}
    query3 = "vue component tutorial"
    context3 = {"query": query3, "user_id": "user_456"}
    
    completed_args3 = await parameter_manager.complete_parameters(
        tool_name3, initial_args3, query3, context3
    )
    
    print(f"工具: {tool_name3}")
    print(f"初始参数: {initial_args3}")
    print(f"查询: {query3}")
    print(f"补全后参数: {completed_args3}")
    print(f"用户习惯: {parameter_manager.user_habits}")
    
    print("\n" + "="*60)
    print("测试3: 相似任务迁移")
    print("="*60)
    
    # 测试相似任务迁移
    tool_name4 = "resolve-library-id"
    initial_args4 = {}
    query4 = "react component patterns"  # 与历史查询相似
    context4 = {"query": query4, "user_id": "user_789"}
    
    completed_args4 = await parameter_manager.complete_parameters(
        tool_name4, initial_args4, query4, context4
    )
    
    print(f"工具: {tool_name4}")
    print(f"初始参数: {initial_args4}")
    print(f"查询: {query4}")
    print(f"补全后参数: {completed_args4}")
    
    print("\n" + "="*60)
    print("测试4: 参数模式更新")
    print("="*60)
    
    # 测试参数模式更新
    print(f"更新前模式数量: {len(parameter_manager.parameter_patterns)}")
    
    parameter_manager.update_parameter_patterns(
        "resolve-library-id",
        {"libraryName": "angular"},
        {"query": "angular dependency injection", "user_id": "user_123"},
        success=True
    )
    
    print(f"更新后模式数量: {len(parameter_manager.parameter_patterns)}")
    print("参数模式存储:")
    for key, patterns in parameter_manager.parameter_patterns.items():
        print(f"  {key}: {len(patterns)} 个模式")
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_parameter_manager_enhanced())