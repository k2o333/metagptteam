#!/usr/bin/env python3
"""
测试知识管理功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT.parent))

from hierarchical.actions.knowledge_manager import KnowledgeManager, CaseRecord

async def test_knowledge_manager():
    """测试知识管理器"""
    print("🧪 测试知识管理器...")
    
    # 创建知识管理器实例
    km = KnowledgeManager()
    
    # 测试数据
    task_info_1 = {
        "task_id": "task_001",
        "description": "How to use React hooks effectively in functional components",
        "user_id": "user_123",
        "task_type": "development",
        "keywords": ["react", "hooks", "functional components"]
    }
    
    execution_result_1 = {
        "parameters": {
            "libraryName": "react",
            "topic": "hooks"
        },
        "tools_used": ["resolve-library-id", "get-library-docs"],
        "execution_steps": [
            {
                "step": 1,
                "action": "resolve-library-id",
                "parameters": {"libraryName": "react"}
            },
            {
                "step": 2,
                "action": "get-library-docs",
                "parameters": {
                    "context7CompatibleLibraryID": "/vercel/next.js",
                    "topic": "hooks"
                }
            }
        ],
        "quality_score": 0.95,
        "execution_time": 15.2,
        "resource_usage": {
            "cpu_percent": 45,
            "memory_mb": 120
        }
    }
    
    task_info_2 = {
        "task_id": "task_002",
        "description": "Implementing state management with Redux in React applications",
        "user_id": "user_123",
        "task_type": "development",
        "keywords": ["react", "redux", "state management"]
    }
    
    execution_result_2 = {
        "parameters": {
            "libraryName": "redux",
            "topic": "state management"
        },
        "tools_used": ["resolve-library-id", "get-library-docs", "resolve-library-id"],
        "execution_steps": [
            {
                "step": 1,
                "action": "resolve-library-id",
                "parameters": {"libraryName": "redux"}
            },
            {
                "step": 2,
                "action": "get-library-docs",
                "parameters": {
                    "context7CompatibleLibraryID": "/reduxjs/redux",
                    "topic": "state management"
                }
            },
            {
                "step": 3,
                "action": "resolve-library-id",
                "parameters": {"libraryName": "react-redux"}
            }
        ],
        "quality_score": 0.88,
        "execution_time": 22.5,
        "resource_usage": {
            "cpu_percent": 52,
            "memory_mb": 150
        }
    }
    
    print("\n" + "="*60)
    print("测试1: 案例归档")
    print("="*60)
    
    # 测试案例归档
    success1 = await km.archive_case(task_info_1, execution_result_1)
    print(f"案例1归档结果: {'成功' if success1 else '失败'}")
    
    success2 = await km.archive_case(task_info_2, execution_result_2)
    print(f"案例2归档结果: {'成功' if success2 else '失败'}")
    
    print(f"当前案例库大小: {len(km.experience_repo.case_database)}")
    
    # 显示归档的案例
    for case_id, case_record in km.experience_repo.case_database.items():
        print(f"  案例ID: {case_record.case_id}")
        print(f"    描述: {case_record.task_description}")
        print(f"    工具: {case_record.tools_used}")
        print(f"    质量分数: {case_record.quality_score}")
        print(f"    标签: {case_record.tags}")
    
    print("\n" + "="*60)
    print("测试2: 相似案例检索")
    print("="*60)
    
    # 测试相似案例检索
    current_task = {
        "description": "How to manage state in React applications using hooks",
        "keywords": ["react", "state management", "hooks"],
        "complexity": "medium"
    }
    
    similar_cases = await km.experience_repo.retrieve_similar_cases(current_task, limit=3)
    print(f"找到 {len(similar_cases)} 个相似案例:")
    
    for i, case in enumerate(similar_cases):
        print(f"  相似案例 {i+1}:")
        print(f"    ID: {case.case_id}")
        print(f"    描述: {case.task_description}")
        print(f"    相似度: 计算中...")
        print(f"    工具: {case.tools_used}")
        print(f"    质量: {case.quality_score}")
    
    print("\n" + "="*60)
    print("测试3: 智能推荐")
    print("="*60)
    
    # 测试智能推荐
    recommendations = await km.get_recommendations(current_task, user_id="user_123")
    print("智能推荐结果:")
    
    print(f"  相似案例数量: {len(recommendations['similar_cases'])}")
    print(f"  个性化建议数量: {len(recommendations['personalized_suggestions'])}")
    print(f"  解决方案模板数量: {len(recommendations['solution_templates'])}")
    
    # 显示个性化建议
    print("  个性化建议:")
    for suggestion in recommendations['personalized_suggestions']:
        print(f"    类型: {suggestion['type']}")
        print(f"    描述: {suggestion['description']}")
        if 'recommendations' in suggestion:
            print(f"    推荐: {suggestion['recommendations']}")
        if 'patterns' in suggestion:
            print(f"    模式: {suggestion['patterns']}")
        if 'suggestions' in suggestion:
            print(f"    建议: {suggestion['suggestions']}")
    
    # 显示解决方案模板
    print("  解决方案模板:")
    for template in recommendations['solution_templates']:
        print(f"    模板ID: {template['template_id']}")
        print(f"    描述: {template['description']}")
        print(f"    常用参数: {template['common_parameters']}")
        print(f"    典型工具序列: {template['typical_tool_sequence']}")
        print(f"    成功因素: {template['success_factors']}")
        print(f"    潜在陷阱: {template['potential_pitfalls']}")
    
    print("\n" + "="*60)
    print("测试4: 用户画像")
    print("="*60)
    
    # 测试用户画像
    user_id = "user_123"
    if user_id in km.experience_repo.user_profiles:
        user_profile = km.experience_repo.user_profiles[user_id]
        print(f"用户ID: {user_profile.user_id}")
        print(f"最后更新: {user_profile.last_updated}")
        print(f"行为历史记录数量: {len(user_profile.behavior_history)}")
        print(f"成功模式数量: {len(user_profile.success_patterns)}")
        
        print("  成功模式:")
        for pattern in user_profile.success_patterns[-3:]:  # 显示最近3个
            print(f"    - {pattern}")
    else:
        print(f"未找到用户 {user_id} 的画像")
    
    print("\n" + "="*60)
    print("测试5: 交互学习")
    print("="*60)
    
    # 测试交互学习
    interaction_data = {
        "task_info": {
            "task_id": "task_003",
            "description": "Building responsive layouts with CSS Grid and Flexbox",
            "user_id": "user_456",
            "task_type": "frontend",
            "keywords": ["css", "grid", "flexbox", "responsive"]
        },
        "execution_result": {
            "parameters": {
                "libraryName": "css",
                "topic": "layout"
            },
            "tools_used": ["resolve-library-id", "get-library-docs"],
            "execution_steps": [
                {
                    "step": 1,
                    "action": "resolve-library-id",
                    "parameters": {"libraryName": "css"}
                },
                {
                    "step": 2,
                    "action": "get-library-docs",
                    "parameters": {
                        "context7CompatibleLibraryID": "/w3c/css",
                        "topic": "layout"
                    }
                }
            ],
            "quality_score": 0.92,
            "execution_time": 18.7,
            "resource_usage": {
                "cpu_percent": 38,
                "memory_mb": 95
            }
        },
        "user_feedback": {
            "rating": 5,
            "comments": "Very helpful information about CSS layout techniques"
        }
    }
    
    learning_success = await km.learn_from_interaction(interaction_data)
    print(f"交互学习结果: {'成功' if learning_success else '失败'}")
    
    print(f"更新后案例库大小: {len(km.experience_repo.case_database)}")
    
    # 显示新增的案例
    if km.experience_repo.case_database:
        latest_case_id = list(km.experience_repo.case_database.keys())[-1]
        latest_case = km.experience_repo.case_database[latest_case_id]
        print(f"最新案例ID: {latest_case.case_id}")
        print(f"  描述: {latest_case.task_description}")
        print(f"  工具: {latest_case.tools_used}")
        print(f"  质量分数: {latest_case.quality_score}")
        print(f"  标签: {latest_case.tags}")
    
    print("\n" + "="*60)
    print("测试6: 知识图谱")
    print("="*60)
    
    # 测试知识图谱
    kg = km.experience_repo.knowledge_graph
    print(f"知识图谱实体数量: {len(kg.entities)}")
    print(f"知识图谱关系数量: {len(kg.relationships)}")
    
    print("  实体示例:")
    for entity_id, entity_data in list(kg.entities.items())[:5]:
        print(f"    {entity_id}: {entity_data}")
    
    print("  关系示例:")
    for relation in kg.relationships[:3]:
        print(f"    {relation['source']} --{relation['type']}--> {relation['target']} (权重: {relation['weight']})")
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_knowledge_manager())