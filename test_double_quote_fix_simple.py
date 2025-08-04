#!/usr/bin/env python3
"""
测试双引号修复功能 - 简化版本
"""

import re
import json

def test_double_quote_fix():
    """测试双引号修复功能"""
    
    def preprocess_decision_string(decision_str: str) -> str:
        """预处理决策字符串（从research_controller.py复制简化版本）"""
        if not decision_str:
            return "{}"
        
        # 移除markdown代码块标记
        decision_str = re.sub(r'```json\s*', '', decision_str)
        decision_str = re.sub(r'\s*```', '', decision_str)
        
        # 移除不可见字符
        decision_str = decision_str.strip()
        decision_str = decision_str.replace('\ufeff', '')
        decision_str = decision_str.replace('\u200b', '')
        
        # 特殊处理：修复双引号问题
        # 简化策略：直接处理所有重复双引号的情况
        
        # 1. 首先处理最简单的情况：全局替换 ""key"" 为 "key"
        decision_str = re.sub(r'"{2}([^"]+)"{2}', r'"\1"', decision_str)
        decision_str = re.sub(r'"{3}([^"]+)"{3}', r'"\1"', decision_str)
        
        # 2. 修复单引号包裹的键名 ('key' -> "key")
        decision_str = re.sub(r"'([^']+)'(\s*:)", r'"\1"\2', decision_str)
        
        # 3. 特殊处理：如果修复后仍然有重复双引号问题，进行更精细的处理
        # 检查是否还有未解决的重复双引号
        if '""' in decision_str:
            # 处理键位置的重复双引号
            decision_str = re.sub(r'"{2,3}([^"]+)"{2,3}(\s*:)', r'"\1"\2', decision_str)
            # 处理值位置的重复双引号
            decision_str = re.sub(r':\s*"{2,3}([^"]+)"{2,3}(\s*[,}])', r': "\1"\2', decision_str)
        
        # 替换常见的JSON格式问题
        decision_str = decision_str.replace("'", '"')
        decision_str = re.sub(r',\s*}', '}', decision_str)
        decision_str = re.sub(r',\s*]', ']', decision_str)
        
        # 确保action对象正确格式化
        # 更简单直接的方法：全局替换所有重复双引号问题
        # 修复任何位置的 ""key"" 模式为 "key"
        decision_str = re.sub(r'"{2}([^"]+)"{2}', r'"\1"', decision_str)
        # 修复任何位置的 """key""" 模式为 "key"
        decision_str = re.sub(r'"{3}([^"]+)"{3}', r'"\1"', decision_str)
        
        # 特殊处理：修复可能的误匹配，确保不在字符串内容中替换
        # 只替换在键位置的双引号（后跟冒号）
        decision_str = re.sub(r'"{2,3}([^"]+)"{2,3}(\s*:)', r'"\1"\2', decision_str)
        # 只替换在值位置的双引号（前跟冒号）
        decision_str = re.sub(r':\s*"{2,3}([^"]+)"{2,3}(\s*[,}])', r': "\1"\2', decision_str)
        
        return decision_str
    
    # 测试用例 - 简化版本，专注于测试实际问题
    test_cases = [
        # 实际问题案例
        '''{
  "thought": "To find the documentation for a specific library",
  "action": {
    ""tool_name": ""FINISH""
  }
}''',
        
        # 简单的键名重复双引号
        '''{
  "thought": "Simple test",
  "action": {
    ""tool_name"": "FINISH"
  }
}''',
        
        # 三个引号的情况
        '''{
  "thought": "Three quotes test",
  "action": {
    """tool_name"": ""FINISH""
  }
}''',
        
        # 正常情况
        '''{
  "thought": "Normal case",
  "action": {
    "tool_name": "FINISH"
  }
}''',
    ]
    
    print("Testing simplified double quote fix...")
    success_count = 0
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print("Before fix:")
        print(test_case)
        
        fixed = preprocess_decision_string(test_case)
        print("After fix:")
        print(fixed)
        
        try:
            parsed = json.loads(fixed)
            print("✅ JSON parsing successful!")
            print(f"Parsed thought: {parsed.get('thought', 'N/A')}")
            print(f"Parsed action: {parsed.get('action', 'N/A')}")
            success_count += 1
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
        print("-" * 50)
    
    print(f"\nSummary: {success_count}/{len(test_cases)} test cases passed")
    return success_count == len(test_cases)

if __name__ == "__main__":
    success = test_double_quote_fix()
    if success:
        print("\n🎉 All tests passed! The fix is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Further refinement needed.")