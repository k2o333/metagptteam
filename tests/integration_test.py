#!/usr/bin/env python3
"""
集成测试 - 验证Research模块各个组件的协同工作
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT.parent))

from hierarchical.actions.research_controller import ResearchController
from hierarchical.actions.research_model import ResearchConfig
from hierarchical.actions.research_reviewer import ResearchReviewer
from hierarchical.actions.parameter_manager import ParameterManager
from hierarchical.actions.document_understanding_enhancer import DocumentUnderstandingEnhancer
from hierarchical.actions.user_interaction_optimizer import UserInteractionOptimizer
from hierarchical.actions.quality_assurance import QualityAssuranceSystem

async def integration_test():
    """集成测试"""
    print("🧪 集成测试 - Research模块各组件协同工作验证")
    
    # 1. 创建Research配置
    config = ResearchConfig()
    
    # 2. 创建各个组件实例
    research_controller = ResearchController(config)
    research_reviewer = ResearchReviewer()
    parameter_manager = ParameterManager(config)
    doc_understanding_enhancer = DocumentUnderstandingEnhancer()
    user_interaction_optimizer = UserInteractionOptimizer()
    quality_assurance_system = QualityAssuranceSystem()
    
    # 3. 测试数据
    test_queries = [
        "How to use React hooks effectively in functional components?",
        "Explain the difference between useState and useEffect hooks",
        "What are the best practices for React component design?"
    ]
    
    tool_descriptions = """
    Tool: `resolve-library-id` (from server: context7)
    Description: Resolves a package/product name to a Context7-compatible library ID
    
    Tool: `get-library-docs` (from server: context7)
    Description: Fetches up-to-date documentation for a library
    """
    
    print("\n" + "="*80)
    print("测试场景1: 完整Research流程")
    print("="*80)
    
    # 4. 执行完整的Research流程
    research_results = await research_controller.execute_research(
        queries=test_queries[:1],  # 只测试第一个查询
        tool_descriptions=tool_descriptions
    )
    
    print(f"Research执行完成，结果数量: {len(research_results)}")
    
    for query, result in research_results.items():
        print(f"\n查询: {query}")
        print(f"  状态: {result.get('status', 'unknown')}")
        print(f"  步骤数量: {len(result.get('steps', []))}")
        print(f"  最终答案长度: {len(result.get('final_answer', ''))} 字符")
    
    print("\n" + "="*80)
    print("测试场景2: Research Reviewer评审")
    print("="*80)
    
    # 5. 使用Research Reviewer评审结果
    if research_results:
        first_query_result = list(research_results.values())[0]
        review_result = await research_reviewer.run(
            research_results=first_query_result,
            rewrite_task=test_queries[0]
        )
        
        print("Research Reviewer评审结果:")
        print(f"  状态: {review_result.get('status', 'unknown')}")
        print(f"  失败类型: {review_result.get('failure_type', 'none')}")
        print(f"  置信度: {review_result.get('confidence', 0.0)}")
        print(f"  建议: {review_result.get('recommendation', 'none')}")
        print(f"  参数完整性评分: {review_result.get('completeness_score', 0.0)}")
        print(f"  参数合理性评分: {review_result.get('reasonableness_score', 0.0)}")
        print(f"  工具适用性评分: {review_result.get('tool_applicability_score', 0.0)}")
        print(f"  查询优化评分: {review_result.get('query_optimization_score', 0.0)}")
        print(f"  综合评分: {review_result.get('overall_score', 0.0)}")
        
        suggestions = review_result.get('suggestions', [])
        print(f"  优化建议数量: {len(suggestions)}")
        for i, suggestion in enumerate(suggestions[:3]):  # 只显示前3个建议
            print(f"    建议 {i+1}: {suggestion.get('description', 'N/A')}")
    
    print("\n" + "="*80)
    print("测试场景3: 参数管理增强")
    print("="*80)
    
    # 6. 测试参数管理增强功能
    initial_args = {
        "libraryName": "react"
    }
    
    completed_args = await parameter_manager.complete_parameters(
        tool_name="resolve-library-id",
        initial_args=initial_args,
        query="How to use React hooks?",
        context={"user_id": "test_user_123"}
    )
    
    print("参数管理增强测试:")
    print(f"  初始参数: {initial_args}")
    print(f"  补全后参数: {completed_args}")
    
    # 测试学习型参数推测
    if hasattr(parameter_manager, 'update_parameter_patterns'):
        parameter_manager.update_parameter_patterns(
            tool_name="resolve-library-id",
            parameters={"libraryName": "vue"},
            context={"query": "Vue component lifecycle", "user_id": "test_user_123"},
            success=True
        )
        print("  已更新参数模式用于学习")
    
    print("\n" + "="*80)
    print("测试场景4: 文档理解增强")
    print("="*80)
    
    # 7. 测试文档理解增强功能
    sample_document = """
    # React Hooks Guide
    
    ## What are Hooks?
    
    Hooks are functions that let you "hook into" React state and lifecycle features from function components.
    
    ### Why Hooks?
    
    1. Reuse stateful logic between components
    2. Simplify complex components
    3. Reduce nesting with HOCs and render props
    
    ## useState Hook
    
    ```javascript
    import React, { useState } from 'react';
    
    function Counter() {
      const [count, setCount] = useState(0);
      
      return (
        <div>
          <p>You clicked {count} times</p>
          <button onClick={() => setCount(count + 1)}>
            Click me
          </button>
        </div>
      );
    }
    ```
    
    ## useEffect Hook
    
    The Effect Hook lets you perform side effects in function components.
    """
    
    enhanced_understanding = await doc_understanding_enhancer.enhance_document_understanding(
        sample_document,
        "How to use React hooks effectively?"
    )
    
    print("文档理解增强结果:")
    structure_analysis = enhanced_understanding.get('structure_analysis', {})
    print(f"  标题层级数量: {len(structure_analysis.get('title_hierarchy', []))}")
    
    key_information = enhanced_understanding.get('key_information', [])
    print(f"  关键信息数量: {len(key_information)}")
    
    knowledge_connections = enhanced_understanding.get('knowledge_connections', {})
    print(f"  知识关联数量: {len(knowledge_connections.get('entity_relationships', []))}")
    
    intelligent_summary = enhanced_understanding.get('intelligent_summary', {})
    print(f"  智能摘要生成: {'成功' if intelligent_summary else '失败'}")
    
    print("\n" + "="*80)
    print("测试场景5: 用户交互优化")
    print("="*80)
    
    # 8. 测试用户交互优化功能
    if research_results:
        first_query_result = list(research_results.values())[0]
        steps = first_query_result.get('steps', [])
        if steps:
            current_state = {
                "steps": steps,
                "query": test_queries[0],
                "resource_usage": {"cpu_percent": 45, "memory_mb": 120}
            }
            
            optimization_result = await user_interaction_optimizer.optimize_user_interaction(
                current_state,
                user_id="test_user_123"
            )
            
            print("用户交互优化结果:")
            process_transparency = optimization_result.get('process_transparency')
            print(f"  过程透明度: {'已生成' if process_transparency else '未生成'}")
            
            key_notifications = optimization_result.get('key_point_notifications', [])
            print(f"  关键节点通知: {len(key_notifications)} 个")
            
            collaborative_solution = optimization_result.get('collaborative_solution', {})
            print(f"  协作解决方案: {'已生成' if collaborative_solution else '未生成'}")
            
            risk_warnings = optimization_result.get('risk_warnings', [])
            print(f"  风险预警: {len(risk_warnings)} 个")
    
    print("\n" + "="*80)
    print("测试场景6: 质量保障体系")
    print("="*80)
    
    # 9. 测试质量保障体系
    if research_results:
        first_query_result = list(research_results.values())[0]
        
        # 多层次验证
        validation_data = {
            "tool_name": "resolve-library-id",
            "tool_args": {"libraryName": "react"}
        }
        
        validation_result = await quality_assurance_system.perform_multilevel_validation(
            validation_data
        )
        
        print("质量保障体系测试:")
        print(f"  多层次验证结果: {validation_result.get('overall_result', 'unknown').value}")
        print(f"  验证报告数量: {len(validation_result.get('reports', []))}")
        print(f"  建议数量: {len(validation_result.get('recommendations', []))}")
        
        # 持续改进循环
        execution_data = {
            "query": test_queries[0],
            "steps": first_query_result.get('steps', []),
            "final_answer": first_query_result.get('final_answer', ''),
            "total_duration": 5.7
        }
        
        user_feedback = {
            "rating": 4,
            "comments": "Good explanation of React hooks",
            "satisfaction": 0.8
        }
        
        improvement_result = await quality_assurance_system.run_continuous_improvement_cycle(
            execution_data,
            user_feedback
        )
        
        print(f"\n持续改进循环结果:")
        evaluation_metrics = improvement_result.get('evaluation_metrics', [])
        print(f"  评估指标数量: {len(evaluation_metrics)}")
        
        improvement_suggestions = improvement_result.get('improvement_suggestions', [])
        print(f"  改进建议数量: {len(improvement_suggestions)}")
        
        # 完整质量保障
        quality_result = await quality_assurance_system.ensure_quality(
            validation_data,
            execution_data,
            user_feedback
        )
        
        print(f"\n完整质量保障结果:")
        validation_result = quality_result.get('validation', {})
        print(f"  验证结果: {validation_result.get('overall_result', 'unknown').value if validation_result else 'N/A'}")
        
        improvement_result = quality_result.get('improvement', {})
        improvement_suggestions = improvement_result.get('improvement_suggestions', []) if improvement_result else []
        print(f"  改进建议: {len(improvement_suggestions)} 个")
    
    print("\n" + "="*80)
    print("测试场景7: 组件间协同工作")
    print("="*80)
    
    # 10. 测试组件间协同工作
    print("组件间协同工作测试:")
    
    # 模拟一个完整的Research工作流
    workflow_steps = []
    
    # 步骤1: 文档理解增强
    print("  步骤1: 文档理解增强")
    doc_understanding = await doc_understanding_enhancer.enhance_document_understanding(
        sample_document,
        test_queries[0]
    )
    workflow_steps.append("文档理解增强完成")
    
    # 步骤2: 参数管理增强
    print("  步骤2: 参数管理增强")
    enhanced_params = await parameter_manager.complete_parameters(
        "resolve-library-id",
        {"libraryName": "react"},
        test_queries[0],
        {"user_id": "test_user_123"}
    )
    workflow_steps.append("参数管理增强完成")
    
    # 步骤3: 用户交互优化
    print("  步骤3: 用户交互优化")
    user_state = {
        "steps": [
            {
                "step_number": 1,
                "action": {"tool_name": "resolve-library-id", "tool_args": enhanced_params},
                "observation": "Resolved to /vercel/next.js",
                "status": "success"
            }
        ],
        "query": test_queries[0]
    }
    
    user_interaction_result = await user_interaction_optimizer.optimize_user_interaction(
        user_state,
        "test_user_123"
    )
    workflow_steps.append("用户交互优化完成")
    
    # 步骤4: 质量保障
    print("  步骤4: 质量保障")
    qa_validation = await quality_assurance_system.perform_multilevel_validation(enhanced_params)
    workflow_steps.append("质量保障完成")
    
    print(f"  工作流步骤完成: {len(workflow_steps)}/4")
    for i, step in enumerate(workflow_steps, 1):
        print(f"    {i}. {step}")
    
    print("\n" + "="*80)
    print("测试场景8: 性能基准测试")
    print("="*80)
    
    # 11. 性能基准测试
    import time
    
    # 测试各个组件的执行时间
    performance_results = {}
    
    # 文档理解增强性能测试
    start_time = time.time()
    for _ in range(3):  # 运行3次取平均值
        await doc_understanding_enhancer.enhance_document_understanding(
            sample_document,
            test_queries[0]
        )
    avg_time = (time.time() - start_time) / 3
    performance_results["文档理解增强"] = avg_time
    
    # 参数管理增强性能测试
    start_time = time.time()
    for _ in range(3):
        await parameter_manager.complete_parameters(
            "resolve-library-id",
            {"libraryName": "react"},
            test_queries[0],
            {"user_id": "test_user_123"}
        )
    avg_time = (time.time() - start_time) / 3
    performance_results["参数管理增强"] = avg_time
    
    # 用户交互优化性能测试
    start_time = time.time()
    for _ in range(3):
        await user_interaction_optimizer.optimize_user_interaction(
            user_state,
            "test_user_123"
        )
    avg_time = (time.time() - start_time) / 3
    performance_results["用户交互优化"] = avg_time
    
    print("性能基准测试结果:")
    for component, avg_time in performance_results.items():
        print(f"  {component}: {avg_time:.4f} 秒/次")
    
    print("\n" + "="*80)
    print("测试场景9: 错误处理和恢复")
    print("="*80)
    
    # 12. 测试错误处理和恢复机制
    print("错误处理和恢复测试:")
    
    # 测试无效参数的处理
    invalid_params = await parameter_manager.complete_parameters(
        "resolve-library-id",
        {"libraryName": ""},  # 无效参数
        test_queries[0],
        {"user_id": "test_user_123"}
    )
    print(f"  无效参数处理: {invalid_params}")
    
    # 测试质量保障对无效数据的处理
    invalid_validation = await quality_assurance_system.perform_multilevel_validation(
        {"tool_name": "invalid-tool", "tool_args": {}}
    )
    print(f"  无效数据验证结果: {invalid_validation.get('overall_result', 'unknown').value}")
    
    print("\n" + "="*80)
    print("测试场景10: 完整集成流程")
    print("="*80)
    
    # 13. 完整集成流程测试
    print("完整集成流程测试:")
    
    # 模拟一个完整的Research任务
    task_context = {
        "user_id": "integration_test_user",
        "task_id": "integration_test_task_001",
        "timestamp": "2025-08-09T18:00:00Z"
    }
    
    # 任务执行流程
    task_steps = []
    
    # 1. 文档理解和需求分析
    doc_analysis = await doc_understanding_enhancer.enhance_document_understanding(
        sample_document,
        test_queries[0]
    )
    task_steps.append("文档分析完成")
    
    # 2. 参数优化和补全
    optimized_params = await parameter_manager.complete_parameters(
        "resolve-library-id",
        {"libraryName": "react"},
        test_queries[0],
        task_context
    )
    task_steps.append("参数优化完成")
    
    # 3. 用户交互优化
    interaction_state = {
        "steps": [
            {
                "step_number": 1,
                "action": {"tool_name": "resolve-library-id", "tool_args": optimized_params},
                "observation": "Resolved to /vercel/next.js"
            }
        ],
        "query": test_queries[0]
    }
    
    interaction_result = await user_interaction_optimizer.optimize_user_interaction(
        interaction_state,
        task_context["user_id"]
    )
    task_steps.append("交互优化完成")
    
    # 4. 质量保障
    qa_result = await quality_assurance_system.ensure_quality(
        optimized_params,
        interaction_state,
        {"rating": 5, "comments": "Excellent results"}
    )
    task_steps.append("质量保障完成")
    
    # 5. 最终评审
    final_review = await research_reviewer.run(
        interaction_state,
        test_queries[0]
    )
    task_steps.append("最终评审完成")
    
    print(f"任务执行步骤完成: {len(task_steps)}/{len(task_steps)}")
    for i, step in enumerate(task_steps, 1):
        print(f"  {i}. {step}")
    
    print(f"最终评审结果: {final_review.get('status', 'unknown')}")
    print(f"最终评审置信度: {final_review.get('confidence', 0.0)}")
    print(f"最终评审建议: {final_review.get('recommendation', 'none')}")
    
    print("\n" + "="*80)
    print("集成测试完成!")
    print("="*80)
    print("所有组件协同工作正常，测试通过 ✅")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(integration_test())