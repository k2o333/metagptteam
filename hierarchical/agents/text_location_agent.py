#!/usr/bin/env python3
"""
Text Location Agent based on HierarchicalBaseRole
专门用于精确确认文档中需要修改的位置
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# -----------------

from metagpt.tools.libs.editor import Editor
from metagpt.logs import logger
from metagpt.actions import Action
from metagpt.schema import Message
from hierarchical.roles.base_role import HierarchicalBaseRole


class ConfirmTextLocation(Action):
    """确认文本位置的Action"""
    
    def __init__(self, name: str = "Confirm Text Location", **kwargs):
        super().__init__(name=name, **kwargs)
        self.editor = Editor()
    
    async def run(self, document_path: str, search_text: str, 
                  approximate_line: int = None, approximate_char: int = None,
                  context_chars: int = 100) -> Dict:
        """
        精确确认文本位置
        
        Args:
            document_path: 文档路径
            search_text: 要查找的文本
            approximate_line: LLM提供的近似行号
            approximate_char: LLM提供的近似字符位置
            context_chars: 上下文字符数
            
        Returns:
            Dict with precise location and context info
        """
        logger.info(f"🔍 精确定位文本: '{search_text[:50]}...'")
        
        try:
            # 读取文档内容
            file_content = await self.editor.read(document_path)
            content = file_content.block_content
            
            # 方法1: 直接精确搜索
            direct_result = self._direct_search(content, search_text)
            if direct_result:
                logger.info("✅ 直接搜索成功找到文本")
                return self._add_context_info(content, direct_result, context_chars)
            
            # 方法2: 在近似位置附近搜索
            if approximate_line is not None:
                nearby_result = self._search_near_approximate_position(
                    content, search_text, approximate_line)
                if nearby_result:
                    logger.info("✅ 在近似位置附近找到文本")
                    return self._add_context_info(content, nearby_result, context_chars)
            
            # 方法3: 模糊搜索
            fuzzy_result = self._fuzzy_search(content, search_text)
            if fuzzy_result:
                logger.info("✅ 模糊搜索找到文本")
                return self._add_context_info(content, fuzzy_result, context_chars)
                
            # 未找到
            logger.error(f"❌ 未找到文本: '{search_text}'")
            return {
                "found": False,
                "error": f"未找到文本: '{search_text}'",
                "search_text": search_text
            }
            
        except Exception as e:
            logger.error(f"精确定位时出错: {e}")
            return {
                "found": False,
                "error": f"定位错误: {str(e)}",
                "search_text": search_text
            }
    
    def _direct_search(self, content: str, search_text: str) -> Optional[Dict]:
        """直接精确搜索"""
        pos = content.find(search_text)
        if pos != -1:
            return self._calculate_location(content, pos, len(search_text))
        return None
    
    def _search_near_approximate_position(self, content: str, search_text: str, 
                                        approx_line: int) -> Optional[Dict]:
        """在近似位置附近搜索"""
        lines = content.splitlines()
        if approx_line < 0 or approx_line >= len(lines):
            return None
            
        # 搜索范围：前后5行
        start_line = max(0, approx_line - 5)
        end_line = min(len(lines) - 1, approx_line + 5)
        
        # 构造搜索范围的内容
        search_range_content = "\n".join(lines[start_line:end_line + 1])
        pos_in_range = search_range_content.find(search_text)
        
        if pos_in_range != -1:
            # 计算在整个文档中的位置
            lines_before = "\n".join(lines[:start_line])
            if lines_before:
                full_pos = len(lines_before) + 1 + pos_in_range  # +1 for newline
            else:
                full_pos = pos_in_range
            return self._calculate_location(content, full_pos, len(search_text))
            
        return None
    
    def _fuzzy_search(self, content: str, search_text: str) -> Optional[Dict]:
        """模糊搜索"""
        # 使用正则表达式，允许空白字符变化
        escaped_text = re.escape(search_text)
        # 允许一些空白字符变化
        pattern = escaped_text.replace(r'\ ', r'\s*')
        
        match = re.search(pattern, content)
        if match:
            return self._calculate_location(content, match.start(), match.end() - match.start())
        return None
    
    def _calculate_location(self, content: str, start_pos: int, length: int) -> Dict:
        """计算位置信息"""
        text_before_start = content[:start_pos]
        start_line = text_before_start.count('\n')
        
        last_newline_start = text_before_start.rfind('\n')
        if last_newline_start == -1:
            start_char = start_pos
        else:
            start_char = start_pos - last_newline_start - 1
            
        end_pos = start_pos + length
        text_before_end = content[:end_pos]
        end_line = text_before_end.count('\n')
        
        last_newline_end = text_before_end.rfind('\n')
        if last_newline_end == -1:
            end_char = end_pos
        else:
            end_char = end_pos - last_newline_end - 1
            
        # Fix for edge case: when we're at the beginning of the content
        # start_char and end_char should be relative to the line start
        lines = content.splitlines(keepends=True)
        if start_line < len(lines):
            line_start_pos = sum(len(line) for line in lines[:start_line])
            start_char = start_pos - line_start_pos
        if end_line < len(lines):
            line_start_pos = sum(len(line) for line in lines[:end_line])
            end_char = end_pos - line_start_pos
            
        return {
            "found": True,
            "start_line": start_line,
            "start_char": start_char,
            "end_line": end_line,
            "end_char": end_char,
            "start_pos": start_pos,
            "end_pos": end_pos,
            "length": length
        }
    
    def _add_context_info(self, content: str, location: Dict, context_chars: int) -> Dict:
        """添加上下文信息"""
        if not location.get("found"):
            return location
            
        start_pos = location["start_pos"]
        # 提取前后上下文
        context_start = max(0, start_pos - context_chars)
        context_end = min(len(content), start_pos + location["length"] + context_chars)
        
        context = content[context_start:context_end]
        
        location["context"] = context
        location["context_start_pos"] = context_start
        location["context_end_pos"] = context_end
        
        return location


class TextLocationAgent(HierarchicalBaseRole):
    """精确定位文本的Agent"""
    
    name: str = "TextLocationAgent"
    profile: str = "Precise Text Location Agent"
    goal: str = "Accurately locate text positions in documents for precise replacement"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 添加确认文本位置的Action
        self.set_actions([ConfirmTextLocation()])
        self._watch(["TextLocationRequest", "UserRequirement", "LocationVerificationRequest"])
        logger.info(f"📝 TextLocationAgent initialized with name='{self.name}', profile='{self.profile}'")
        
    async def _think(self) -> bool:
        """思考要执行的任务"""
        logger.info(f"🔄 TextLocationAgent._think() called with {len(self.rc.news) if self.rc.news else 0} messages")
        if self.rc.news:
            logger.info(f"🔄 TextLocationAgent._think(): News messages: {len(self.rc.news)}")
            for i, msg in enumerate(self.rc.news):
                logger.info(f"  📬 Message {i}: cause_by={msg.cause_by}, role={msg.role}, send_to={msg.send_to}")
        if not self.rc.news:
            logger.info("🔄 TextLocationAgent._think(): No news messages")
            return False
            
        latest_msg = self.rc.news[-1]
        logger.info(f"🔄 TextLocationAgent._think(): Latest message cause_by={latest_msg.cause_by}, role={latest_msg.role}, content={latest_msg.content[:100]}...")
        
        if latest_msg.cause_by in ["TextLocationRequest", "UserRequirement", "LocationVerificationRequest"]:
            self.rc.todo = "CONFIRM_TEXT_LOCATION"
            logger.info("✅ TextLocationAgent._think(): Setting todo to CONFIRM_TEXT_LOCATION")
            return True
            
        logger.info(f"🔄 TextLocationAgent._think(): Message not matched, cause_by={latest_msg.cause_by}")
        return False
    
    async def _act(self) -> Message:
        """执行精确定位任务"""
        logger.info(f"--- {self.name} 正在执行精确定位 ---")
        
        await self._think()
        logger.info(f"--- {self.name} _think completed, todo={self.rc.todo} ---")
        
        if self.rc.todo != "CONFIRM_TEXT_LOCATION":
            logger.info(f"--- {self.name} No task to perform, todo={self.rc.todo} ---")
            return None
            
        latest_msg = self.rc.news[-1]
        
        try:
            # 解析请求数据
            request_data = json.loads(latest_msg.content)
            document_path = request_data.get("document_path")
            search_text = request_data.get("search_text")
            approx_line = request_data.get("approximate_line")
            approx_char = request_data.get("approximate_char")
            task_index = request_data.get("task_index")
            
            if not document_path or not search_text:
                return Message(
                    content="错误: 缺少文档路径或搜索文本",
                    role=self.profile,
                    send_to="ChangeCoordinator"
                )
            
            # 执行精确定位
            confirm_action = self.actions[0]  # ConfirmTextLocation
            result = await confirm_action.run(
                document_path=document_path,
                search_text=search_text,
                approximate_line=approx_line,
                approximate_char=approx_char
            )
            
            # Add task index to result
            result["task_index"] = task_index
            
            # 返回结果
            return Message(
                content=json.dumps(result, ensure_ascii=False),
                role=self.profile,
                send_to="ChangeCoordinator",
                cause_by="TextLocationConfirmed"
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"解析请求数据失败: {e}")
            return Message(
                content=f"错误: 解析请求数据失败: {e}",
                role=self.profile,
                send_to="ChangeCoordinator"
            )
        except Exception as e:
            logger.error(f"执行精确定位时出错: {e}")
            return Message(
                content=f"错误: 执行精确定位时出错: {e}",
                role=self.profile,
                send_to="ChangeCoordinator"
            )


def main():
    """测试精确定位Agent"""
    print("Text Location Agent 测试")
    
    # 这里可以添加测试代码
    agent = TextLocationAgent()
    print(f"Agent创建成功: {agent.name}")


if __name__ == "__main__":
    main()