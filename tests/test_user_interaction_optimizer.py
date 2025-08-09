#!/usr/bin/env python3
"""
测试用户交互优化功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT.parent))

from hierarchical.actions.user_interaction_optimizer import (
    UserInteractionOptimizer, 
    TransparencyLevel,
    ProcessVisualization,
    KeyPointNotification,
    ProgressiveInquiry,
    MultiOptionProposal,
    RiskWarning
)

async def test_user_interaction_optimizer():
    """测试用户交互优化器"""
    print("🧪 测试用户交互优化器...")
    
    # 创建用户交互优化器实例
    uio = UserInteractionOptimizer(TransparencyLevel.HIGH)
    
    # 测试数据
    react_step_1 = {
        "step_number": 1,
        "thought": "I need to identify the React library to understand how to use hooks effectively. This involves resolving the library ID first.",
        "action": {
            "tool_name": "resolve-library-id",
            "tool_args": {"libraryName": "react"}
        },
        "observation": "Resolved to /vercel/next.js",
        "confidence": 0.9,
        "duration": 2.5
    }
    
    react_step_2 = {
        "step_number": 2,
        "thought": "Now that I have the library ID, I need to get the documentation about React hooks to understand their usage.",
        "action": {
            "tool_name": "get-library-docs",
            "tool_args": {
                "context7CompatibleLibraryID": "/vercel/next.js",
                "topic": "hooks"
            }
        },
        "observation": "Found documentation about React hooks including useState, useEffect, and custom hooks.",
        "confidence": 0.85,
        "duration": 3.2
    }
    
    react_cycle_state = {
        "query": "How to use React hooks effectively in functional components?",
        "steps": [react_step_1, react_step_2],
        "resource_usage": {
            "cpu_percent": 45,
            "memory_mb": 120
        },
        "total_duration": 5.7
    }
    
    current_state = {
        "query": "How to use React hooks effectively in functional components?",
        "steps": [react_step_1, react_step_2],
        "resource_usage": {
            "cpu_percent": 45,
            "memory_mb": 120
        }
    }
    
    print("\n" + "="*60)
    print("测试1: 过程透明度增强")
    print("="*60)
    
    # 测试过程透明度增强
    process_viz_1 = await uio.enhance_process_transparency(react_step_1, user_id="user_123")
    print(f"步骤1过程可视化:")
    print(f"  步骤编号: {process_viz_1.step_number}")
    print(f"  思考过程: {process_viz_1.thought[:50]}...")
    print(f"  行动: {process_viz_1.action}")
    print(f"  置信度: {process_viz_1.confidence_level}")
    print(f"  推理链长度: {len(process_viz_1.reasoning_chain)}")
    
    process_viz_2 = await uio.enhance_process_transparency(react_step_2, user_id="user_123")
    print(f"\n步骤2过程可视化:")
    print(f"  步骤编号: {process_viz_2.step_number}")
    print(f"  思考过程: {process_viz_2.thought[:50]}...")
    print(f"  行动: {process_viz_2.action}")
    print(f"  置信度: {process_viz_2.confidence_level}")
    print(f"  推理链长度: {len(process_viz_2.reasoning_chain)}")
    
    print("\n" + "="*60)
    print("测试2: 关键决策通知")
    print("="*60)
    
    # 测试关键决策通知
    key_notifications = await uio.notify_key_decisions(react_cycle_state, user_id="user_123")
    print(f"生成 {len(key_notifications)} 个关键决策通知:")
    
    for i, notification in enumerate(key_notifications):
        print(f"  通知 {i+1}:")
        print(f"    ID: {notification.notification_id}")
        print(f"    决策点: {notification.decision_point}")
        print(f"    影响: {notification.decision_impact}")
        print(f"    用户邀请: {notification.user_invitation[:50]}...")
    
    print("\n" + "="*60)
    print("测试3: 协作式问题解决")
    print("="*60)
    
    # 测试协作式问题解决
    collaboration_result = await uio.solve_collaboratively(current_state, user_id="user_123")
    print("协作式问题解决结果:")
    
    inquiry = collaboration_result.get("inquiry")
    if inquiry:
        print(f"  渐进式询问:")
        print(f"    ID: {inquiry['inquiry_id']}")
        print(f"    问题数量: {len(inquiry['questions'])}")
        print(f"    重要性级别: {inquiry['importance_level']}")
        
        for j, question in enumerate(inquiry['questions']):
            print(f"      问题 {j+1}: {question['question'][:50]}...")
    
    proposal = collaboration_result.get("proposal")
    if proposal:
        print(f"  多选项提案:")
        print(f"    ID: {proposal['proposal_id']}")
        print(f"    选项数量: {len(proposal['options'])}")
        print(f"    排名数量: {len(proposal['comparison_analysis'].get('rankings', []))}")
        
        for k, option in enumerate(proposal['options']):
            print(f"      选项 {k+1}: {option['name']} (置信度: {option['confidence']})")
    
    print("\n" + "="*60)
    print("测试4: 风险监控和预警")
    print("="*60)
    
    # 测试风险监控和预警
    risks = await uio.monitor_and_warn_risks(react_cycle_state, user_id="user_123")
    print(f"检测到 {len(risks)} 个潜在风险:")
    
    for i, risk in enumerate(risks):
        print(f"  风险 {i+1}:")
        print(f"    ID: {risk.warning_id}")
        print(f"    类型: {risk.risk_type}")
        print(f"    严重性: {risk.severity}")
        print(f"    预测影响: {risk.predicted_impact}")
        print(f"    缓解策略数量: {len(risk.mitigation_strategies)}")
    
    print("\n" + "="*60)
    print("测试5: 完整用户交互优化")
    print("="*60)
    
    # 测试完整用户交互优化
    optimization_result = await uio.optimize_user_interaction(current_state, user_id="user_123")
    print("完整用户交互优化结果:")
    
    process_transparency = optimization_result.get("process_transparency")
    if process_transparency:
        print(f"  过程透明度: 已生成")
        print(f"    步骤: {process_transparency['step_number']}")
        print(f"    行动: {process_transparency['action'].get('tool_name', 'N/A')}")
    
    key_notifications = optimization_result.get("key_point_notifications", [])
    print(f"  关键节点通知: {len(key_notifications)} 个")
    
    collaborative_solution = optimization_result.get("collaborative_solution", {})
    if collaborative_solution:
        print(f"  协作解决方案: 已生成")
        inquiry = collaborative_solution.get("inquiry")
        if inquiry:
            print(f"    渐进式询问: {len(inquiry.get('questions', []))} 个问题")
        proposal = collaborative_solution.get("proposal")
        if proposal:
            print(f"    多选项提案: {len(proposal.get('options', []))} 个选项")
    
    risk_warnings = optimization_result.get("risk_warnings", [])
    print(f"  风险预警: {len(risk_warnings)} 个")
    
    print(f"  优化时间: {optimization_result.get('optimization_timestamp', 'N/A')}")
    
    print("\n" + "="*60)
    print("测试6: 透明度级别测试")
    print("="*60)
    
    # 测试不同透明度级别
    transparency_levels = [TransparencyLevel.LOW, TransparencyLevel.MEDIUM, TransparencyLevel.HIGH]
    
    for level in transparency_levels:
        print(f"\n测试透明度级别: {level.value}")
        uio_low = UserInteractionOptimizer(level)
        process_viz = await uio_low.enhance_process_transparency(react_step_1, user_id="user_123")
        
        if process_viz:
            viz_content = uio_low.transparency_manager._generate_visualization_content({
                "step_number": process_viz.step_number,
                "thought": process_viz.thought,
                "action": process_viz.action,
                "confidence_level": process_viz.confidence_level,
                "reasoning_chain": process_viz.reasoning_chain,
                "timestamp": process_viz.timestamp
            })
            print(f"  可视化内容类型: {viz_content.get('type', 'N/A')}")
            print(f"  包含字段: {list(viz_content.keys())}")
    
    print("\n" + "="*60)
    print("测试7: 复杂度风险检测")
    print("="*60)
    
    # 测试复杂度风险检测
    complex_react_cycle_state = {
        "query": "Build a complete web application with React, Redux, Node.js, Express, MongoDB, and Docker",
        "steps": [
            {"step_number": 1, "action": {"tool_name": "resolve-library-id"}, "status": "completed"},
            {"step_number": 2, "action": {"tool_name": "get-library-docs"}, "status": "completed"},
            {"step_number": 3, "action": {"tool_name": "resolve-library-id"}, "status": "completed"},
            {"step_number": 4, "action": {"tool_name": "get-library-docs"}, "status": "completed"},
            {"step_number": 5, "action": {"tool_name": "resolve-library-id"}, "status": "completed"},
            {"step_number": 6, "action": {"tool_name": "get-library-docs"}, "status": "completed"},
            {"step_number": 7, "action": {"tool_name": "resolve-library-id"}, "status": "completed"},
            {"step_number": 8, "action": {"tool_name": "get-library-docs"}, "status": "completed"},
            {"step_number": 9, "action": {"tool_name": "resolve-library-id"}, "status": "completed"},
            {"step_number": 10, "action": {"tool_name": "get-library-docs"}, "status": "completed"},
        ],
        "resource_usage": {
            "cpu_percent": 85,
            "memory_mb": 550
        },
        "total_duration": 125
    }
    
    complex_risks = await uio.risk_warning_system.detect_potential_risks(complex_react_cycle_state)
    print(f"复杂任务检测到 {len(complex_risks)} 个风险:")
    
    for i, risk in enumerate(complex_risks):
        print(f"  风险 {i+1}:")
        print(f"    类型: {risk.risk_type}")
        print(f"    严重性: {risk.severity}")
        print(f"    预测影响: {risk.predicted_impact}")
        print(f"    缓解策略: {len(risk.mitigation_strategies)} 条")
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_user_interaction_optimizer())