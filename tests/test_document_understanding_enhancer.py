#!/usr/bin/env python3
"""
测试文档理解增强功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT.parent))

from hierarchical.actions.document_understanding_enhancer import DocumentUnderstandingEnhancer

async def test_document_understanding_enhancer():
    """测试文档理解增强功能"""
    print("🧪 测试文档理解增强功能...")
    
    # 创建增强器实例
    enhancer = DocumentUnderstandingEnhancer()
    
    # 测试文档内容
    test_document = """
# React Hooks指南

## 什么是Hooks?

Hooks是React 16.8版本引入的新特性，它让你在不编写class的情况下使用state以及其他的React特性。

### 为什么引入Hooks?

1. 组件之间复用状态逻辑很难
2. 复杂组件难以理解
3. class组件学习成本高

## useState Hook

```javascript
import React, { useState } from 'react';

function Example() {
  // 声明一个叫 "count" 的 state 变量
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

useEffect Hook 可以让你在函数组件中执行副作用操作。

### 基本用法

```javascript
import React, { useState, useEffect } from 'react';

function Example() {
  const [count, setCount] = useState(0);

  // 相当于 componentDidMount 和 componentDidUpdate:
  useEffect(() => {
    // 使用浏览器的 API 更新页面标题
    document.title = `You clicked ${count} times`;
  });

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

## 自定义Hook

当我们想在两个函数之间共享逻辑时，可以提取到自定义Hook中。

### 创建自定义Hook

```javascript
import { useState, useEffect } from 'react';

function useFriendStatus(friendID) {
  const [isOnline, setIsOnline] = useState(null);

  useEffect(() => {
    function handleStatusChange(status) {
      setIsOnline(status.isOnline);
    }

    ChatAPI.subscribeToFriendStatus(friendID, handleStatusChange);
    return () => {
      ChatAPI.unsubscribeFromFriendStatus(friendID, handleStatusChange);
    };
  });

  return isOnline;
}
```

## 最佳实践

1. 只在最顶层调用Hook
2. 只在React函数组件中调用Hook
3. 使用ESLint插件确保Hook规则
"""
    
    # 测试用户查询
    test_queries = [
        "How to use React useState hook?",
        "What are React Hooks and why do we need them?",
        "Explain useEffect hook with examples",
        "Best practices for React Hooks"
    ]
    
    print("\n" + "="*60)
    print("测试1: 文档结构分析")
    print("="*60)
    
    structure_analysis = enhancer.analyze_document_structure(test_document)
    print(f"标题层级: {len(structure_analysis['title_hierarchy'])} 个标题")
    print(f"关键章节: {len(structure_analysis['key_sections'])} 个关键章节")
    print(f"逻辑流程: {'检测到' if structure_analysis['logical_flow']['has_logical_flow'] else '未检测到'}逻辑流程")
    
    for title in structure_analysis['title_hierarchy'][:5]:  # 只显示前5个标题
        print(f"  - Level {title['level']}: {title['text']}")
    
    print("\n" + "="*60)
    print("测试2: 用户需求解析")
    print("="*60)
    
    for query in test_queries:
        user_requirements = enhancer.parse_user_requirements(query)
        print(f"查询: {query}")
        print(f"  核心意图: {user_requirements.core_intent['type']} - {user_requirements.core_intent['content']}")
        print(f"  约束条件: {user_requirements.constraints}")
        print(f"  优先级: {user_requirements.priorities}")
        print()
    
    print("\n" + "="*60)
    print("测试3: 关键信息提取")
    print("="*60)
    
    key_information = enhancer.extract_key_information(test_document)
    print(f"提取到 {len(key_information)} 个关键信息项")
    
    code_blocks = [info for info in key_information if info["type"] == "code"]
    concepts = [info for info in key_information if info["type"] == "concept"]
    list_items = [info for info in key_information if info["type"] == "list_item"]
    
    print(f"  代码块: {len(code_blocks)} 个")
    print(f"  概念: {len(concepts)} 个")
    print(f"  列表项: {len(list_items)} 个")
    
    print("\n" + "="*60)
    print("测试4: 知识关联建立")
    print("="*60)
    
    knowledge_connections = enhancer.establish_knowledge_connections(structure_analysis, key_information)
    print(f"实体关系: {len(knowledge_connections['entity_relationships'])} 个")
    print(f"概念层次: 深度 {knowledge_connections['concept_hierarchy']['hierarchy_depth']}")
    print(f"交叉引用: {len(knowledge_connections['cross_references'])} 个")
    
    print("\n" + "="*60)
    print("测试5: 智能摘要生成")
    print("="*60)
    
    # 使用第一个查询进行测试
    user_requirements = enhancer.parse_user_requirements(test_queries[0])
    intelligent_summary = enhancer.create_intelligent_summary(
        structure_analysis, key_information, knowledge_connections, user_requirements
    )
    
    print("文档概览:")
    print(f"  {intelligent_summary['document_overview']}")
    
    print("关键点:")
    for point in intelligent_summary['key_points'][:3]:  # 只显示前3个关键点
        print(f"  - {point}")
    
    print("主要概念:")
    for concept in intelligent_summary['main_concepts'][:5]:  # 只显示前5个概念
        print(f"  - {concept}")
    
    print("用户指导:")
    print(f"  {intelligent_summary['user_guidance']}")
    
    print("导航建议:")
    for suggestion in intelligent_summary['navigation_suggestions']:
        print(f"  - {suggestion}")
    
    print("\n" + "="*60)
    print("测试6: 完整增强流程")
    print("="*60)
    
    # 测试完整的增强流程
    enhanced_result = await enhancer.enhance_document_understanding(test_document, test_queries[0])
    
    print(f"增强完成时间: {enhanced_result['enhancement_timestamp']}")
    print(f"结构分析完成: {len(enhanced_result['structure_analysis']['title_hierarchy'])} 个标题")
    print(f"关键信息提取: {len(enhanced_result['key_information'])} 项")
    print(f"知识关联建立: {len(enhanced_result['knowledge_connections']['entity_relationships'])} 个关系")
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_document_understanding_enhancer())