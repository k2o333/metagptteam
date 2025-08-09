#!/usr/bin/env python3
"""
测试ReAct循环优化功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT.parent))

from hierarchical.actions.react_optimizer import ReActOptimizer, GoalOrientedPlanner, AdaptiveStrategyAdjuster

async def test_react_optimizer():
    """测试ReAct优化器"""
    print("🧪 测试ReAct循环优化器...")
    
    # 创建优化器实例
    optimizer = ReActOptimizer()
    
    # 测试数据
    test_query = "How to use React hooks effectively in functional components?"
    
    # 模拟ReAct循环状态
    react_cycle_state = {
        "query": test_query,
        "steps": [
            {
                "step_number": 1,
                "thought": "Need to understand what React hooks are",
                "action": {
                    "tool_name": "resolve-library-id",
                    "tool_args": {"libraryName": "react"}
                },
                "observation": "Resolved to /vercel/next.js",
                "status": "completed"
            },
            {
                "step_number": 2,
                "thought": "Need to get documentation about React hooks",
                "action": {
                    "tool_name": "get-library-docs",
                    "tool_args": {
                        "context7CompatibleLibraryID": "/vercel/next.js",
                        "topic": "hooks"
                    }
                },
                "observation": "Found documentation about React hooks...",
                "status": "completed"
            }
        ],
        "context_history": [
            {
                "step": 1,
                "context": "Step 1: Need to understand what React hooks are",
                "timestamp": "2025-08-09T10:00:00"
            },
            {
                "step": 2,
                "context": "Step 2: Need to get documentation about React hooks",
                "timestamp": "2025-08-09T10:01:00"
            }
        ],
        "error_log": [],
        "executed_steps": 2,
        "max_loops": 10
    }
    
    print("\n" + "="*60)
    print("测试1: 目标导向规划")
    print("="*60)
    
    # 测试目标导向规划
    goal_planner = GoalOrientedPlanner()
    planning_result = await goal_planner.goal_oriented_action_planning(
        test_query, react_cycle_state
    )
    
    print(f"查询: {test_query}")
    print(f"已执行步骤: {len(react_cycle_state['steps'])}")
    print(f"最优路径: {planning_result['optimal_path'].get('path_id', 'N/A')}")
    print(f"替代路径数量: {len(planning_result['alternative_paths'])}")
    
    print("\n子目标分解:")
    for i, sub_goal in enumerate(planning_result['planning_metadata']['goal_decomposition']):
        print(f"  {i+1}. {sub_goal['category']}: {sub_goal['description']}")
    
    print("\n" + "="*60)
    print("测试2: 自适应策略调整")
    print("="*60)
    
    # 测试自适应策略调整
    strategy_adjuster = AdaptiveStrategyAdjuster()
    strategy_result = await strategy_adjuster.adaptive_strategy_adjustment(react_cycle_state)
    
    complexity_assessment = strategy_result['complexity_assessment']
    print(f"复杂度评估:")
    print(f"  分数: {complexity_assessment['score']}")
    print(f"  级别: {complexity_assessment['level']}")
    print(f"  因素: {complexity_assessment['factors']}")
    
    strategy_adjustments = strategy_result['strategy_adjustments']
    print(f"\n策略调整:")
    print(f"  复杂度级别: {strategy_adjustments['complexity_level']}")
    print(f"  推荐策略: {strategy_adjustments['recommended_strategy']}")
    
    for adjustment in strategy_adjustments['adjustments']:
        print(f"  - {adjustment['type']}: {adjustment['description']}")
    
    print("\n" + "="*60)
    print("测试3: 完整ReAct优化")
    print("="*60)
    
    # 测试完整优化
    optimization_result = await optimizer.optimize_react_cycle(test_query, react_cycle_state)
    
    print(f"优化时间: {optimization_result['optimization_timestamp']}")
    
    # 打印规划结果
    planning = optimization_result['planning']
    print(f"\n规划结果:")
    print(f"  最优路径ID: {planning['optimal_path'].get('path_id', 'N/A')}")
    print(f"  评估时间: {planning['planning_metadata']['evaluation_timestamp']}")
    
    # 打印策略结果
    strategy = optimization_result['strategy']
    print(f"\n策略结果:")
    print(f"  复杂度级别: {strategy['complexity_assessment']['level']}")
    print(f"  调整时间: {strategy['adjustment_timestamp']}")
    
    print("\n" + "="*60)
    print("测试4: 目标分解功能")
    print("="*60)
    
    # 测试目标分解
    sub_goals = await goal_planner.decompose_goal(test_query, react_cycle_state)
    print(f"查询: {test_query}")
    print(f"分解出 {len(sub_goals)} 个子目标:")
    
    for i, goal in enumerate(sub_goals):
        print(f"  {i+1}. {goal['category']}: {goal['description']} (优先级: {goal['priority']})")
    
    print("\n" + "="*60)
    print("测试5: 复杂度评估")
    print("="*60)
    
    # 测试复杂度评估
    complexity = await strategy_adjuster.assess_task_complexity(react_cycle_state)
    print(f"复杂度评估结果:")
    print(f"  分数: {complexity['score']}")
    print(f"  级别: {complexity['level']}")
    print(f"  评估时间: {complexity['assessment_timestamp']}")
    
    print(f"\n复杂度因素:")
    for factor, value in complexity['factors'].items():
        print(f"  {factor}: {value}")
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_react_optimizer())