#!/usr/bin/env python3
"""
测试质量保障功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT.parent))

from hierarchical.actions.quality_assurance import (
    QualityAssuranceSystem,
    ValidationLevel,
    ValidationResult,
    MultiLevelValidator,
    ContinuousImprovementLoop
)

async def test_quality_assurance():
    """测试质量保障系统"""
    print("🧪 测试质量保障系统...")
    
    # 创建质量保障系统实例
    qa_system = QualityAssuranceSystem()
    
    # 测试数据
    valid_data = {
        "tool_name": "resolve-library-id",
        "tool_args": {
            "libraryName": "react"
        }
    }
    
    invalid_data = {
        "tool_name": "resolve-library-id",
        "tool_args": {
            "libraryName": ""  # 空值，会导致验证失败
        }
    }
    
    business_invalid_data = {
        "tool_name": "resolve-library-id",
        "tool_args": {
            "libraryName": "system"  # 受限的库名称
        }
    }
    
    execution_data = {
        "query": "How to use React hooks effectively?",
        "steps": [
            {
                "step_number": 1,
                "action": {
                    "tool_name": "resolve-library-id",
                    "tool_args": {"libraryName": "react"}
                },
                "observation": "Resolved to /vercel/next.js",
                "status": "success",
                "duration": 2.5
            },
            {
                "step_number": 2,
                "action": {
                    "tool_name": "get-library-docs",
                    "tool_args": {
                        "context7CompatibleLibraryID": "/vercel/next.js",
                        "topic": "hooks"
                    }
                },
                "observation": "Found documentation about React hooks",
                "status": "success",
                "duration": 3.2
            }
        ],
        "final_answer": "React hooks are a powerful feature that allow you to use state and other React features without writing a class.",
        "total_duration": 5.7
    }
    
    user_feedback = {
        "rating": 4,
        "comments": "Good explanation of React hooks, but could include more examples",
        "satisfaction": 0.8,
        "improvement_areas": ["More practical examples", "Better code samples"]
    }
    
    print("\n" + "="*60)
    print("测试1: 多层次验证器")
    print("="*60)
    
    # 测试多层次验证器
    validator = MultiLevelValidator()
    
    # 语法验证
    syntax_report = await validator.validate(valid_data, ValidationLevel.SYNTAX)
    print(f"语法验证结果: {syntax_report.result.value}")
    print(f"  验证ID: {syntax_report.validation_id}")
    print(f"  验证器: {syntax_report.validator_name}")
    
    # 语义验证
    semantic_report = await validator.validate(valid_data, ValidationLevel.SEMANTIC)
    print(f"\n语义验证结果: {semantic_report.result.value}")
    print(f"  验证ID: {semantic_report.validation_id}")
    print(f"  验证器: {semantic_report.validator_name}")
    
    # 业务验证
    business_report = await validator.validate(valid_data, ValidationLevel.BUSINESS)
    print(f"\n业务验证结果: {business_report.result.value}")
    print(f"  验证ID: {business_report.validation_id}")
    print(f"  验证器: {business_report.validator_name}")
    
    print("\n" + "="*60)
    print("测试2: 无效数据验证")
    print("="*60)
    
    # 测试无效数据验证
    invalid_syntax_report = await validator.validate(invalid_data, ValidationLevel.SYNTAX)
    print(f"无效数据语法验证结果: {invalid_syntax_report.result.value}")
    
    invalid_semantic_report = await validator.validate(invalid_data, ValidationLevel.SEMANTIC)
    print(f"无效数据语义验证结果: {invalid_semantic_report.result.value}")
    
    invalid_business_report = await validator.validate(invalid_data, ValidationLevel.BUSINESS)
    print(f"无效数据业务验证结果: {invalid_business_report.result.value}")
    
    print("\n" + "="*60)
    print("测试3: 受限数据验证")
    print("="*60)
    
    # 测试受限数据验证
    business_invalid_report = await validator.validate(business_invalid_data, ValidationLevel.BUSINESS)
    print(f"受限数据业务验证结果: {business_invalid_report.result.value}")
    if business_invalid_report.details:
        print(f"  详情: {business_invalid_report.details}")
    
    print("\n" + "="*60)
    print("测试4: 多层次验证")
    print("="*60)
    
    # 测试多层次验证
    multilevel_result = await qa_system.perform_multilevel_validation(valid_data)
    print(f"多层次验证总体结果: {multilevel_result['overall_result'].value}")
    print(f"  报告数量: {len(multilevel_result['reports'])}")
    print(f"  建议数量: {len(multilevel_result['recommendations'])}")
    
    for i, report in enumerate(multilevel_result['reports']):
        print(f"  报告 {i+1}:")
        print(f"    级别: {report['level']}")
        print(f"    结果: {report['result']}")
    
    print("\n" + "="*60)
    print("测试5: 多层次验证（无效数据）")
    print("="*60)
    
    # 测试多层次验证（无效数据）
    multilevel_invalid_result = await qa_system.perform_multilevel_validation(invalid_data)
    print(f"无效数据多层次验证总体结果: {multilevel_invalid_result['overall_result'].value}")
    print(f"  报告数量: {len(multilevel_invalid_result['reports'])}")
    print(f"  建议数量: {len(multilevel_invalid_result['recommendations'])}")
    
    if multilevel_invalid_result['recommendations']:
        print("  建议:")
        for recommendation in multilevel_invalid_result['recommendations'][:3]:  # 只显示前3个建议
            print(f"    - {recommendation}")
    
    print("\n" + "="*60)
    print("测试6: 持续改进循环")
    print("="*60)
    
    # 测试持续改进循环
    improvement_result = await qa_system.run_continuous_improvement_cycle(execution_data, user_feedback)
    print("持续改进循环结果:")
    
    evaluation_metrics = improvement_result.get("evaluation_metrics", [])
    print(f"  评估指标数量: {len(evaluation_metrics)}")
    
    for metric in evaluation_metrics:
        print(f"    指标: {metric['name']}")
        print(f"      值: {metric['value']}")
        print(f"      目标: {metric['target']}")
        print(f"      权重: {metric['weight']}")
        print(f"      分类: {metric['category']}")
    
    user_feedback_data = improvement_result.get("user_feedback", {})
    if user_feedback_data:
        print(f"  用户反馈:")
        print(f"    评分: {user_feedback_data.get('user_rating', 'N/A')}")
        print(f"    满意度: {user_feedback_data.get('satisfaction_score', 'N/A')}")
    
    improvement_suggestions = improvement_result.get("improvement_suggestions", [])
    print(f"  改进建议数量: {len(improvement_suggestions)}")
    
    for suggestion in improvement_suggestions[:2]:  # 只显示前2个建议
        print(f"    建议: {suggestion['description']}")
        print(f"      分类: {suggestion['category']}")
        print(f"      优先级: {suggestion['priority']}")
        print(f"      预期收益: {suggestion['expected_benefit']}")
    
    print("\n" + "="*60)
    print("测试7: 完整质量保障")
    print("="*60)
    
    # 测试完整质量保障
    quality_result = await qa_system.ensure_quality(valid_data, execution_data, user_feedback)
    print("完整质量保障结果:")
    
    validation_result = quality_result.get("validation", {})
    if validation_result:
        print(f"  验证结果:")
        print(f"    总体结果: {validation_result.get('overall_result', 'N/A')}")
        print(f"    报告数量: {len(validation_result.get('reports', []))}")
        print(f"    建议数量: {len(validation_result.get('recommendations', []))}")
    
    improvement_result = quality_result.get("improvement", {})
    if improvement_result:
        print(f"  改进结果:")
        print(f"    评估指标: {len(improvement_result.get('evaluation_metrics', []))}")
        print(f"    改进建议: {len(improvement_result.get('improvement_suggestions', []))}")
    
    print(f"  质量保障时间: {quality_result.get('quality_timestamp', 'N/A')}")
    
    print("\n" + "="*60)
    print("测试8: 验证等级测试")
    print("="*60)
    
    # 测试不同验证等级
    validation_levels = [ValidationLevel.SYNTAX, ValidationLevel.SEMANTIC, ValidationLevel.BUSINESS]
    
    for level in validation_levels:
        print(f"\n测试验证等级: {level.value}")
        report = await validator.validate(valid_data, level)
        print(f"  结果: {report.result.value}")
        print(f"  验证器: {report.validator_name}")
        if report.details:
            print(f"  详情字段: {list(report.details.keys())}")
    
    print("\n" + "="*60)
    print("测试9: 性能评估")
    print("="*60)
    
    # 测试性能评估
    improvement_loop = ContinuousImprovementLoop()
    metrics = await improvement_loop.evaluate_performance(execution_data)
    print(f"性能评估指标数量: {len(metrics)}")
    
    for metric in metrics:
        print(f"  指标: {metric.name}")
        print(f"    值: {metric.value}")
        print(f"    目标: {metric.target}")
        print(f"    权重: {metric.weight}")
        print(f"    分类: {metric.category}")
    
    print("\n" + "="*60)
    print("测试10: 反馈收集")
    print("="*60)
    
    # 测试反馈收集
    feedback_data = await improvement_loop.collect_feedback(user_feedback)
    print("反馈收集结果:")
    print(f"  反馈ID: {feedback_data.get('feedback_id', 'N/A')}")
    print(f"  用户评分: {feedback_data.get('user_rating', 'N/A')}")
    print(f"  用户评论: {feedback_data.get('user_comments', 'N/A')[:50]}...")
    print(f"  满意度分数: {feedback_data.get('satisfaction_score', 'N/A')}")
    print(f"  改进领域: {len(feedback_data.get('improvement_areas', []))}")
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_quality_assurance())