#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本，用于验证 ChangeCoordinator 中的研究协调功能
"""

import sys
from pathlib import Path
import asyncio

# Add the root of the MetaGPT project to the Python path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from hierarchical.roles.change_coordinator import ChangeCoordinator
from hierarchical.actions.assess_research_necessity import AssessResearchNecessity


async def test_assess_research_necessity():
    """测试 AssessResearchNecessity Action"""
    print("Testing AssessResearchNecessity Action...")
    
    # 创建一个实例
    action = AssessResearchNecessity()
    
    # 测试数据
    global_topic = "AutoGen AgentChat 教程"
    section_content = "#### 消息 (Message)\n\n消息是代理之间通信的方式。"
    rewrite_instruction = "为每个消息类添加详细注释，说明其用途和关键属性。"
    
    # 执行 action
    result = await action.run(
        global_topic=global_topic,
        section_content=section_content,
        rewrite_instruction=rewrite_instruction
    )
    
    print(f"Assessment result: {result}")
    return result


async def test_change_coordinator_extract_section():
    """测试 ChangeCoordinator 的 _extract_section_content 方法"""
    print("\nTesting ChangeCoordinator _extract_section_content method...")
    
    # 创建一个实例
    coordinator = ChangeCoordinator()
    
    # 设置测试文档内容
    coordinator.document_content = """# AutoGen AgentChat 教程

这是一个关于 AutoGen AgentChat 的教程文档。

## 什么是 AutoGen

AutoGen 是一个框架。

### AutoGen 的核心概念

AutoGen 的核心概念包括代理和消息。

#### 代理 (Agent)

代理是 AutoGen 中的基本构建块。

#### 消息 (Message)

消息是代理之间通信的方式。

## 如何使用 AutoGen

使用 AutoGen 需要创建代理。

### 创建代理

创建代理的步骤如下。

### 配置消息

消息需要正确的配置。"""
    
    # 测试提取章节内容
    heading = "#### 消息 (Message)"
    section_content = coordinator._extract_section_content(heading)
    
    print(f"Extracted section content for '{heading}':\n{section_content}")
    return section_content


async def test_change_coordinator_format_research_results():
    """测试 ChangeCoordinator 的 _format_research_results 方法"""
    print("\nTesting ChangeCoordinator _format_research_results method...")
    
    # 创建一个实例
    coordinator = ChangeCoordinator()
    
    # 测试数据
    results = {
        "AutoGen AgentChat Message class attributes and usage": {
            "status": "success",
            "final_answer": "In AutoGen, messages are used for communication between agents. Key attributes include sender, recipient, content, and timestamp.",
            "steps_taken": 3
        }
    }
    topic = "AutoGen AgentChat Message class attributes and usage"
    
    # 执行方法
    formatted_results = coordinator._format_research_results(results, topic)
    
    print(f"Formatted research results:\n{formatted_results}")
    return formatted_results


async def test_change_coordinator_build_rewrite_prompt():
    """测试 ChangeCoordinator 的 _build_rewrite_prompt 方法"""
    print("\nTesting ChangeCoordinator _build_rewrite_prompt method...")
    
    # 创建一个实例
    coordinator = ChangeCoordinator()
    
    # 测试数据
    section_content = "#### 消息 (Message)\n\n消息是代理之间通信的方式。"
    rewrite_task = "为每个消息类添加详细注释，说明其用途和关键属性。"
    research_context = "研究发现：\nIn AutoGen, messages are used for communication between agents. Key attributes include sender, recipient, content, and timestamp.\n"
    
    # 执行方法
    prompt_with_context = coordinator._build_rewrite_prompt(section_content, rewrite_task, research_context)
    prompt_without_context = coordinator._build_rewrite_prompt(section_content, rewrite_task, "")
    
    print(f"Rewrite prompt with context:\n{prompt_with_context}\n")
    print(f"Rewrite prompt without context:\n{prompt_without_context}")
    return prompt_with_context, prompt_without_context


async def test_change_coordinator_clean_rewritten_content():
    """测试 ChangeCoordinator 的 _clean_rewritten_content 方法"""
    print("\nTesting ChangeCoordinator _clean_rewritten_content method...")
    
    # 创建一个实例
    coordinator = ChangeCoordinator()
    
    # 测试数据
    content_with_heading = """#### 消息 (Message)
这是重写后的内容，包含关于消息类的详细注释。
消息类用于代理之间的通信，具有发送者、接收者、内容和时间戳等关键属性。"""
    
    content_without_heading = """这是重写后的内容，包含关于消息类的详细注释。
消息类用于代理之间的通信，具有发送者、接收者、内容和时间戳等关键属性。"""
    
    heading = "#### 消息 (Message)"
    
    # 执行方法
    cleaned_with_heading = coordinator._clean_rewritten_content(content_with_heading, heading)
    cleaned_without_heading = coordinator._clean_rewritten_content(content_without_heading, heading)
    
    print(f"Cleaned content (with heading):\n{cleaned_with_heading}\n")
    print(f"Cleaned content (without heading):\n{cleaned_without_heading}")
    return cleaned_with_heading, cleaned_without_heading


async def main():
    """主测试函数"""
    print("Starting comprehensive tests for research coordination functionality...")
    
    # 测试 AssessResearchNecessity
    assessment_result = await test_assess_research_necessity()
    
    # 测试 ChangeCoordinator 的章节提取
    section_content = await test_change_coordinator_extract_section()
    
    # 测试 ChangeCoordinator 的研究结果格式化
    formatted_results = await test_change_coordinator_format_research_results()
    
    # 测试 ChangeCoordinator 的重写提示构建
    prompt_with_context, prompt_without_context = await test_change_coordinator_build_rewrite_prompt()
    
    # 测试 ChangeCoordinator 的重写内容清理
    cleaned_with_heading, cleaned_without_heading = await test_change_coordinator_clean_rewritten_content()
    
    print("\nAll tests completed.")
    
    # 验证结果
    print(f"\nValidation:")
    print(f"1. AssessResearchNecessity returned a dict with 'should_research': {'should_research' in assessment_result}")
    print(f"2. Section content extracted successfully: {len(section_content) > 0}")
    print(f"3. Research results formatted successfully: {len(formatted_results) > 0}")
    print(f"4. Rewrite prompts built successfully: {len(prompt_with_context) > 0 and len(prompt_without_context) > 0}")
    print(f"5. Content cleaned successfully: {len(cleaned_with_heading) > 0 and len(cleaned_without_heading) > 0}")


if __name__ == "__main__":
    asyncio.run(main())