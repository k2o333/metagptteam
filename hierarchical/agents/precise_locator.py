#!/usr/bin/env python3
"""
Precise Text Locator Agent
专门用于精确确认文档中需要修改的位置
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from metagpt.logs import logger


class PreciseTextLocator:
    """精确文本定位器"""
    
    def __init__(self):
        self.name = "PreciseTextLocator"
        self.profile = "Precise Text Locator Agent"
        self.goal = "Accurately locate text positions in documents for precise replacement"
    
    def locate_text_precisely(self, document_content: str, search_text: str, 
                            approximate_line: int = None, approximate_char: int = None) -> Optional[Dict]:
        """
        精确查找文本位置
        
        Args:
            document_content: 文档内容
            search_text: 要查找的文本
            approximate_line: LLM提供的近似行号
            approximate_char: LLM提供的近似字符位置
            
        Returns:
            Dict with precise location info or None if not found
        """
        logger.info(f"精确查找文本: '{search_text[:50]}...'")
        
        # 方法1: 直接查找
        lines = document_content.splitlines(keepends=True)
        full_content = document_content
        
        # 直接搜索文本
        start_pos = full_content.find(search_text)
        if start_pos != -1:
            # 计算精确位置
            location = self._calculate_precise_location(full_content, start_pos, len(search_text))
            if location:
                # 验证位置正确性
                extracted_text = self._extract_text_at_location(lines, location)
                if extracted_text == search_text:
                    logger.info(f"✅ 精确找到文本位置: 行{location['start_line']}, 字符{location['start_char']}")
                    return location
                else:
                    logger.warning("❌ 位置验证失败，提取的文本不匹配")
        
        # 方法2: 如果提供了近似位置，在附近搜索
        if approximate_line is not None and approximate_char is not None:
            logger.info(f"在近似位置附近搜索: 行{approximate_line}, 字符{approximate_char}")
            nearby_text = self._search_nearby_position(lines, search_text, approximate_line, approximate_char)
            if nearby_text:
                return nearby_text
        
        # 方法3: 使用正则表达式模糊匹配
        logger.info("尝试正则表达式模糊匹配")
        fuzzy_match = self._fuzzy_search_with_regex(full_content, search_text)
        if fuzzy_match:
            return fuzzy_match
            
        logger.error(f"❌ 未找到文本: '{search_text}'")
        return None
    
    def _calculate_precise_location(self, full_content: str, start_pos: int, text_length: int) -> Dict:
        """计算精确位置信息"""
        # 计算起始位置
        text_before_start = full_content[:start_pos]
        start_line = text_before_start.count('\n')
        
        last_newline_start = text_before_start.rfind('\n')
        if last_newline_start == -1:
            start_char = start_pos
        else:
            start_char = start_pos - last_newline_start - 1
            
        # 计算结束位置
        end_pos = start_pos + text_length
        text_before_end = full_content[:end_pos]
        end_line = text_before_end.count('\n')
        
        last_newline_end = text_before_end.rfind('\n')
        if last_newline_end == -1:
            end_char = end_pos
        else:
            end_char = end_pos - last_newline_end - 1
            
        return {
            "start_line": start_line,
            "start_char": start_char,
            "end_line": end_line,
            "end_char": end_char
        }
    
    def _extract_text_at_location(self, lines: List[str], location: Dict) -> str:
        """在指定位置提取文本"""
        try:
            start_line = location["start_line"]
            start_char = location["start_char"]
            end_line = location["end_line"]
            end_char = location["end_char"]
            
            if start_line == end_line:
                return lines[start_line][start_char:end_char]
            else:
                # 多行提取
                parts = []
                parts.append(lines[start_line][start_char:])
                for i in range(start_line + 1, end_line):
                    parts.append(lines[i])
                parts.append(lines[end_line][:end_char])
                return "".join(parts)
        except Exception as e:
            logger.error(f"提取文本时出错: {e}")
            return ""
    
    def _search_nearby_position(self, lines: List[str], search_text: str, 
                              approx_line: int, approx_char: int) -> Optional[Dict]:
        """在近似位置附近搜索"""
        # 搜索范围：前后5行
        search_range = 5
        start_line = max(0, approx_line - search_range)
        end_line = min(len(lines) - 1, approx_line + search_range)
        
        for line_idx in range(start_line, end_line + 1):
            line_content = lines[line_idx]
            # 在当前行中搜索
            pos = line_content.find(search_text)
            if pos != -1:
                logger.info(f"在附近找到文本: 行{line_idx}, 位置{pos}")
                return {
                    "start_line": line_idx,
                    "start_char": pos,
                    "end_line": line_idx,
                    "end_char": pos + len(search_text)
                }
        
        return None
    
    def _fuzzy_search_with_regex(self, full_content: str, search_text: str) -> Optional[Dict]:
        """使用正则表达式进行模糊搜索"""
        # 将搜索文本转换为更宽松的正则表达式
        # 允许空白字符变化
        escaped_text = re.escape(search_text)
        # 允许空白字符的一些变化
        pattern = escaped_text.replace(r'\ ', r'\s+')
        
        match = re.search(pattern, full_content)
        if match:
            start_pos = match.start()
            text_length = match.end() - start_pos
            location = self._calculate_precise_location(full_content, start_pos, text_length)
            logger.info(f"正则表达式匹配成功: {location}")
            return location
            
        return None
    
    def get_context_around_position(self, document_content: str, location: Dict, 
                                  context_length: int = 100) -> Dict:
        """获取指定位置周围的上下文"""
        lines = document_content.splitlines(keepends=True)
        
        try:
            # 提取当前位置的文本
            current_text = self._extract_text_at_location(lines, location)
            
            # 获取前后上下文
            start_line = max(0, location["start_line"] - 3)
            end_line = min(len(lines) - 1, location["end_line"] + 3)
            
            context_lines = lines[start_line:end_line + 1]
            context_text = "".join(context_lines)
            
            return {
                "current_text": current_text,
                "context": context_text,
                "start_line_in_context": location["start_line"] - start_line,
                "position_info": f"行{location['start_line']}, 字符{location['start_char']}"
            }
        except Exception as e:
            logger.error(f"获取上下文时出错: {e}")
            return {
                "current_text": "",
                "context": "",
                "start_line_in_context": 0,
                "position_info": "未知位置"
            }


def main():
    """测试精确定位器"""
    print("Precise Text Locator Agent 测试")
    
    # 测试文档
    test_doc = """# Test Document

This is a simple test document.
It has multiple lines.
We want to find specific text.

## Section
This is the text we want to locate exactly."""

    locator = PreciseTextLocator()
    
    # 测试1: 精确查找
    print("\n=== 测试1: 精确查找 ===")
    result = locator.locate_text_precisely(test_doc, "specific text")
    if result:
        print(f"找到位置: {result}")
        context = locator.get_context_around_position(test_doc, result)
        print(f"上下文: {context['context'][:200]}...")
    
    # 测试2: 带近似位置的查找
    print("\n=== 测试2: 带近似位置的查找 ===")
    result = locator.locate_text_precisely(test_doc, "text we want", 5, 10)
    if result:
        print(f"找到位置: {result}")
        context = locator.get_context_around_position(test_doc, result)
        print(f"上下文: {context['context'][:200]}...")


if __name__ == "__main__":
    main()