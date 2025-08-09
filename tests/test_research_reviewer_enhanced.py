#!/usr/bin/env python3
"""
测试增强版Research Reviewer功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT.parent))

from hierarchical.actions.research_reviewer import ResearchReviewer

async def test_research_reviewer_enhanced():
    """测试增强版Research Reviewer"""
    print("🧪 测试增强版Research Reviewer...")
    
    # 创建Reviewer实例
    reviewer = ResearchReviewer()
    
    # 测试数据1: 包含参数缺失的研究结果
    research_results_1 = {
        "query_1": {
            "status": "success",
            "final_answer": "This is a test research result with some content.",
            "steps": [
                {
                    "step_number": 1,
                    "thought": "Need to resolve library ID for react",
                    "action": {
                        "tool_name": "resolve-library-id",
                        "tool_args": {
                            "libraryName": "react"
                        }
                    },
                    "observation": "Resolved to /vercel/next.js"
                },
                {
                    "step_number": 2,
                    "thought": "Need to get library docs",
                    "action": {
                        "tool_name": "get-library-docs",
                        "tool_args": {
                            "context7CompatibleLibraryID": "/vercel/next.js",
                            "topic": None  # 缺失参数
                        }
                    },
                    "observation": "Got documentation content"
                }
            ]
        }
    }
    
    # 测试数据2: 包含不合理参数的研究结果
    research_results_2 = {
        "query_2": {
            "status": "success",
            "final_answer": "This is another test research result.",
            "steps": [
                {
                    "step_number": 1,
                    "thought": "Need to resolve library ID",
                    "action": {
                        "tool_name": "resolve-library-id",
                        "tool_args": {
                            "libraryName": "a" * 1500  # 过长的参数值
                        }
                    },
                    "observation": "Resolved library ID"
                }
            ]
        }
    }
    
    # 测试数据3: 正常的研究结果
    research_results_3 = {
        "query_3": {
            "status": "success",
            "final_answer": "This is a well-formed research result with good content quality and relevance.",
            "steps": [
                {
                    "step_number": 1,
                    "thought": "Need to resolve library ID for react documentation",
                    "action": {
                        "tool_name": "resolve-library-id",
                        "tool_args": {
                            "libraryName": "react"
                        }
                    },
                    "observation": "Resolved to /vercel/next.js"
                },
                {
                    "step_number": 2,
                    "thought": "Need to get library docs about hooks",
                    "action": {
                        "tool_name": "get-library-docs",
                        "tool_args": {
                            "context7CompatibleLibraryID": "/vercel/next.js",
                            "topic": "hooks"
                        }
                    },
                    "observation": "Got documentation content about React hooks"
                }
            ]
        }
    }
    
    # 测试数据4: 空的研究结果
    research_results_4 = {}
    
    # 测试用的重写任务
    rewrite_task = "Explain how to use React hooks in functional components"
    
    print("\n" + "="*60)
    print("测试1: 参数完整性分析")
    print("="*60)
    
    result1 = await reviewer.run(research_results_1, rewrite_task)
    print(f"审核状态: {result1['status']}")
    print(f"综合评分: {result1['overall_score']}")
    print(f"参数完整性评分: {result1['completeness_score']}")
    print(f"参数合理性评分: {result1['reasonableness_score']}")
    print(f"工具适用性评分: {result1['tool_applicability_score']}")
    print(f"查询优化评分: {result1['query_optimization_score']}")
    print("优化建议:")
    for suggestion in result1['suggestions']:
        print(f"  - [{suggestion['type']}] {suggestion['description']}")
        print(f"    建议: {suggestion['suggestion']}")
    
    print("\n" + "="*60)
    print("测试2: 参数合理性分析")
    print("="*60)
    
    result2 = await reviewer.run(research_results_2, rewrite_task)
    print(f"审核状态: {result2['status']}")
    print(f"综合评分: {result2['overall_score']}")
    print(f"参数完整性评分: {result2['completeness_score']}")
    print(f"参数合理性评分: {result2['reasonableness_score']}")
    print("优化建议:")
    for suggestion in result2['suggestions']:
        print(f"  - [{suggestion['type']}] {suggestion['description']}")
        print(f"    建议: {suggestion['suggestion']}")
    
    print("\n" + "="*60)
    print("测试3: 正常研究结果审核")
    print("="*60)
    
    result3 = await reviewer.run(research_results_3, rewrite_task)
    print(f"审核状态: {result3['status']}")
    print(f"综合评分: {result3['overall_score']}")
    print(f"参数完整性评分: {result3['completeness_score']}")
    print(f"参数合理性评分: {result3['reasonableness_score']}")
    print(f"工具适用性评分: {result3['tool_applicability_score']}")
    print(f"查询优化评分: {result3['query_optimization_score']}")
    print(f"置信度: {result3['confidence']}")
    print("优化建议:")
    for suggestion in result3['suggestions']:
        print(f"  - [{suggestion['type']}] {suggestion['description']}")
        print(f"    建议: {suggestion['suggestion']}")
    
    print("\n" + "="*60)
    print("测试4: 空研究结果审核")
    print("="*60)
    
    result4 = await reviewer.run(research_results_4, rewrite_task)
    print(f"审核状态: {result4['status']}")
    print(f"失败类型: {result4['failure_type']}")
    print("优化建议:")
    for suggestion in result4['suggestions']:
        print(f"  - [{suggestion['type']}] {suggestion['description']}")
        print(f"    建议: {suggestion['suggestion']}")

    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_research_reviewer_enhanced())