#!/usr/bin/env python3
"""
测试双引号修复功能 - 最终版本
"""

import re
import json

def test_double_quote_fix():
    """测试双引号修复功能"""
    
    def preprocess_decision_string(decision_str: str) -> str:
        """预处理决策字符串（从research_controller.py复制最新版本）"""
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
        # 主要策略：移除多余的双引号，保持JSON结构完整
        
        # 1. 修复键名周围的双引号问题 (""key" -> "key")
        decision_str = re.sub(r'"{2}([^"]+)"{2}(\s*:)', r'"\1"\2', decision_str)
        decision_str = re.sub(r'"{3}([^"]+)"{3}(\s*:)', r'"\1"\2', decision_str)
        
        # 2. 修复值周围的双引号问题 (": ""value"" -> ": "value")
        decision_str = re.sub(r':\s*"{2}([^"]+)"{2}(\s*[,}])', r': "\1"\2', decision_str)
        decision_str = re.sub(r':\s*"{3}([^"]+)"{3}(\s*[,}])', r': "\1"\2', decision_str)
        
        # 3. 特殊处理thought字段 - 先修复字段名周围的双引号
        decision_str = re.sub(r'("thought"\s*:\s*)"{2,3}', r'\1"', decision_str, flags=re.IGNORECASE)
        
        # 4. 修复单引号包裹的键名 ('key' -> "key")
        decision_str = re.sub(r"'([^']+)'(\s*:)", r'"\1"\2', decision_str)
        
        # 5. 处理thought字段内容的转义（简化处理，避免过度转义）
        # 只在thought字段值包含未转义引号时进行处理
        if '"thought"' in decision_str.lower():
            # 使用更保守的方法处理thought内容
            thought_match = re.search(r'"thought"\s*:\s*"([^"]*)"', decision_str, re.IGNORECASE)
            if thought_match:
                original_content = thought_match.group(1)
                # 如果内容中包含双引号，进行转义
                if '"' in original_content:
                    escaped_content = original_content.replace('"', '\\"')
                    decision_str = re.sub(
                        r'("thought"\s*:\s*)"[^"]*"',
                        f'\\1"{escaped_content}"',
                        decision_str,
                        flags=re.IGNORECASE
                    )
        
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
    
    # 测试用例 - 从原始日志中提取的实际问题案例
    test_cases = [
        # 原始问题案例 - 简化版本，模拟日志中的情况
        '''{
  "thought": "To find the documentation for a specific library, I need to first resolve the library ID using the provided library name. I will start with React.",
  "action": {
    ""tool_name": ""FINISH""
  }
}''',
        
        # 嵌套对象的重复双引号问题
        '''{
  "thought": "Starting research process",
  "action": {
    ""tool_name": ""resolve-library-id"",
    ""tool_args": {
      ""library_name": ""React""
    }
  }
}''',
        
        # 三个引号的情况
        '''{
  "thought": "Complex research process",
  "action": {
    """tool_name"": ""FINISH""
  }
}''',
        
        # 正常情况应该保持不变
        '''{
  "thought": "Normal research process",
  "action": {
    "tool_name": "FINISH"
  }
}''',
        
        # 包含引号的thought内容（复杂情况）
        '''{
  "thought": "User asked about \\"React\\" library",
  "action": {
    "tool_name": "FINISH"
  }
}''',
    ]
    
    print("Testing final double quote fix...")
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