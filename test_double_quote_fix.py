#!/usr/bin/env python3
"""
测试双引号修复功能
"""

import re
import json

def test_double_quote_fix():
    """测试双引号修复功能"""
    
    def preprocess_decision_string(decision_str: str) -> str:
        """预处理决策字符串（从research_controller.py复制）"""
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
        # 修复键名周围的重复双引号 (""key"" -> "key") 和 ("""key""" -> "key")
        decision_str = re.sub(r'"{2,3}([^"]+)"{2,3}(\s*:)', r'"\1"\2', decision_str)
        
        # 修复值周围的重复双引号 (: ""value"" -> "value")
        decision_str = re.sub(r':\s*"{2,3}([^"]+)"{2,3}', r': "\1"', decision_str)
        
        # 修复字符串值中的重复引号问题 (Thought: ""content"" -> Thought: "content")
        decision_str = re.sub(r'("thought"\s*:\s*)"{2,3}([^"]+)"{2,3}', r'\1"\2"', decision_str, flags=re.IGNORECASE)
        
        # 修复开头或结尾的多余双引号 (更精确的修复)
        decision_str = re.sub(r'^\s*{\s*"{2,3}', '{ "', decision_str)
        decision_str = re.sub(r'"{2,3}\s*}\s*$', '" }', decision_str)
        
        # 修复单引号包裹的键名 ('key' -> "key")
        decision_str = re.sub(r"'([^']+)'(\s*:)", r'"\1"\2', decision_str)
        
        # 处理thought中的引号问题
        # 确保thought字段正确格式化
        thought_pattern = r'("thought["\s:]*)(["\']?)([^"\n\r]+)(["\']?)'
        def fix_thought_quotes(match):
            prefix = match.group(1)
            content = match.group(3)
            # 转义内容中的双引号
            escaped_content = content.replace('"', '\\"')
            return f'{prefix}"{escaped_content}"'
        
        decision_str = re.sub(thought_pattern, fix_thought_quotes, decision_str, flags=re.IGNORECASE)
        
        # 替换常见的JSON格式问题
        decision_str = decision_str.replace("'", '"')
        decision_str = re.sub(r',\s*}', '}', decision_str)
        decision_str = re.sub(r',\s*]', ']', decision_str)
        
        # 确保action对象正确格式化
        action_pattern = r'("action":\s*){([^}]+)}'
        def fix_action_format(match):
            prefix = match.group(1)
            content = match.group(2)
            # 确保tool_name和tool_args正确格式化
            content = re.sub(r'tool_name["\s:]*["\']?([^"\',]+)["\']?', r'"tool_name": "\1"', content)
            content = re.sub(r'tool_args["\s:]*({[^}]*})', r'"tool_args": \1', content)
            return f'{prefix}{{{content}}}'
        
        decision_str = re.sub(action_pattern, fix_action_format, decision_str)
        
        return decision_str
    
    # 测试用例
    test_cases = [
        # 原始问题案例
        '''{
  "thought": ""To find the documentation for a specific library, I need to first resolve the library ID using the provided library name. I will start with "React"."",
  "action": {
    ""tool_name": ""resolve-library-id"",
    ""tool_args"": {
      ""library_name"": ""React""
    }
  }
}''',
        
        # 三个引号的情况
        '''{
  "thought": """To find the documentation for a specific library, I need to first resolve the library ID using the provided library name. I will start with "React". """,
  "action": {
    """tool_name"": ""FINISH""
  }
}''',
        
        # 混合引号情况
        '''{
  "thought": "Starting research process",
  "action": {
    ""tool_name"": ""FINISH"",
    "result": "Completed"
  }
}''',
    ]
    
    print("Testing double quote fix...")
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
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
        print("-" * 50)

if __name__ == "__main__":
    test_double_quote_fix()