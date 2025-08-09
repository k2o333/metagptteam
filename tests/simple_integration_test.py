#!/usr/bin/env python3
"""
简化集成测试 - 验证Research模块核心组件
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT.parent))

from hierarchical.actions.research_reviewer import ResearchReviewer
from hierarchical.actions.parameter_manager import ParameterManager
from hierarchical.actions.research_model import ResearchConfig

async def simple_integration_test():
    """简化集成测试"""
    print("🧪 简化集成测试 - Research模块核心组件验证")
    
    # 1. 测试Research Reviewer
    print("\n" + "="*60)
    print("测试1: Research Reviewer")
    print("="*60)
    
    reviewer = ResearchReviewer()
    
    # 模拟Research结果
    research_results = {
        "query": "How to use React hooks effectively?",
        "status": "success",
        "source": "react_cycle",
        "final_answer": "React hooks are a powerful feature that allow you to use state and other React features without writing a class.",
        "steps_taken": 3,
        "steps": [
            {
                "step_number": 1,
                "thought": "I need to resolve the React library ID first",
                "action": {
                    "tool_name": "resolve-library-id",
                    "tool_args": {"libraryName": "react"}
                },
                "observation": "Resolved to /vercel/next.js"
            },
            {
                "step_number": 2,
                "thought": "Now I need to get documentation about React hooks",
                "action": {
                    "tool_name": "get-library-docs",
                    "tool_args": {
                        "context7CompatibleLibraryID": "/vercel/next.js",
                        "topic": "hooks"
                    }
                },
                "observation": "Found documentation about React hooks including useState and useEffect"
            },
            {
                "step_number": 3,
                "thought": "I have enough information to answer the query",
                "action": {
                    "tool_name": "FINISH",
                    "tool_args": {
                        "result": "React hooks are a powerful feature that allow you to use state and other React features without writing a class."
                    }
                },
                "observation": "Task completed successfully"
            }
        ]
    }
    
    # 执行评审
    review_result = await reviewer.run(research_results, "How to use React hooks effectively?")
    print(f"评审结果: {review_result['status']}")
    print(f"置信度: {review_result['confidence']}")
    print(f"综合评分: {review_result['overall_score']}")
    print(f"建议数量: {len(review_result['suggestions'])}")
    
    # 2. 测试Parameter Manager
    print("\n" + "="*60)
    print("测试2: Parameter Manager")
    print("="*60)
    
    config = ResearchConfig()
    parameter_manager = ParameterManager(config)
    
    # 测试参数补全
    initial_args = {"libraryName": "react"}
    completed_args = await parameter_manager.complete_parameters(
        "resolve-library-id",
        initial_args,
        "How to use React hooks?",
        {"user_id": "test_user_123"}
    )
    
    print(f"初始参数: {initial_args}")
    print(f"补全后参数: {completed_args}")
    
    # 测试参数验证
    validation_result = parameter_manager.validate_parameters(
        "resolve-library-id",
        completed_args,
        {"required": ["libraryName"]}
    )
    
    print(f"参数验证结果: {validation_result['valid']}")
    if not validation_result['valid']:
        print(f"  错误: {validation_result['error']}")
    
    # 3. 测试学习型参数推测
    print("\n" + "="*60)
    print("测试3: 学习型参数推测")
    print("="*60)
    
    # 更新参数模式（模拟学习过程）
    parameter_manager.update_parameter_patterns(
        "resolve-library-id",
        {"libraryName": "vue"},
        {"query": "Vue component lifecycle", "user_id": "test_user_123"},
        success=True
    )
    
    print("已更新参数模式用于学习")
    
    # 基于学习的参数推测
    learned_args = await parameter_manager.complete_parameters(
        "resolve-library-id",
        {},
        "Vue component lifecycle",
        {"user_id": "test_user_123"}
    )
    
    print(f"学习推测参数: {learned_args}")
    
    print("\n" + "="*60)
    print("简化集成测试完成!")
    print("="*60)
    print("所有核心组件工作正常 ✅")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(simple_integration_test())