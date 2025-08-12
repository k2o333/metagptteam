# /root/metagpt/mghier/hierarchical/roles/section_applier.py
import sys
import json
import re
from pathlib import Path
from typing import Any, Dict, List

# --- Path Setup ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
# -----------------

from metagpt.schema import Message
from metagpt.logs import logger
from hierarchical.roles.base_role import HierarchicalBaseRole
from metagpt.tools.libs.editor import Editor
from metagpt.tools.libs.linter import Linter


def _get_heading_level(line: str) -> int:
    """计算一个 Markdown 标题行的级别。如果不是标题行，返回 0。"""
    line = line.lstrip()
    if not line.startswith('#'):
        return 0
    
    level = 0
    for char in line:
        if char == '#':
            level += 1
        else:
            break
    return level


class SectionApplier(HierarchicalBaseRole):
    """
    SectionApplier Role.
    Applies section changes to Markdown documents based on messages from other roles.
    Uses Editor tool for precise file operations and Linter for validation.
    """
    name: str = "SectionApplier"
    profile: str = "Section Applier"
    goal: str = "Apply section changes to Markdown documents with validation."
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch(["SectionApplicationRequest"])
        self.editor = Editor()
        self.linter = Linter()
        
    async def _think(self) -> bool:
        """
        Determines if there's a section application request to process.
        """
        if not self.rc.news:
            return False
            
        latest_msg = self.rc.news[-1]
        
        if latest_msg.cause_by == "SectionApplicationRequest":
            logger.debug(f"SectionApplier thinking: Found section application request. TODO set to the message itself.")
            self.rc.todo = "APPLY_SECTION"
            return True
        
        logger.debug(f"SectionApplier thinking: Latest message is not a section application request. No action needed.")
        return False
        
    async def _act(self) -> Message:
        logger.info(f"--- {self.name} is acting... ---")
        
        await self._think()
        if self.rc.todo != "APPLY_SECTION":
            logger.warning("SectionApplier activated but has no task. Skipping.")
            return None
            
        latest_msg = self.rc.news[-1]
            
        try:
            content_data = json.loads(latest_msg.content)
            target_heading_string = content_data.get("target_heading_string")
            new_heading_and_content = content_data.get("new_heading_and_content")
            file_path = content_data.get("file_path")
            
            if not all([target_heading_string, new_heading_and_content, file_path]):
                error_msg = "Error: Missing required data in section application request."
                logger.error(error_msg)
                self._send_completion_message(error_msg, "failed", target_heading_string, file_path)
                return Message(content=error_msg, role=self.profile, send_to="ChangeCoordinator")
            
            doc_path = Path(file_path)
            if not doc_path.exists():
                error_msg = f"Error: Document file not found: {file_path}"
                logger.error(error_msg)
                self._send_completion_message(error_msg, "failed", target_heading_string, file_path)
                return Message(content=error_msg, role=self.profile, send_to="ChangeCoordinator")
                
            document_content = doc_path.read_text(encoding='utf-8')
            lines = document_content.splitlines(keepends=True)
            
            target_level = _get_heading_level(target_heading_string)
            start_line_idx = -1
            end_line_idx = len(lines) # 默认为文件末尾

            # 1. 找到起始行
            for i, line in enumerate(lines):
                if line.strip() == target_heading_string.strip():
                    start_line_idx = i
                    break
            
            if start_line_idx == -1:
                error_msg = f"Error: Target heading not found in document: {target_heading_string}"
                logger.error(error_msg)
                self._send_completion_message(error_msg, "failed", target_heading_string, file_path)
                return Message(content=error_msg, role=self.profile, send_to="ChangeCoordinator")

            # 2. 从起始行下一行开始，找到结束行
            for i in range(start_line_idx + 1, len(lines)):
                line = lines[i]
                level = _get_heading_level(line)
                if 0 < level <= target_level:
                    end_line_idx = i
                    break
            
            # 3. 构造旧的文本块
            old_section_block = "".join(lines[start_line_idx:end_line_idx])
            
            # 4. 执行替换
            # 我们在旧块的末尾添加一个换行符，以确保替换后格式正确
            # 同时确保新内容也以换行符结尾
            if not new_heading_and_content.endswith('\n'):
                new_heading_and_content += '\n'
                
            modified_content = document_content.replace(old_section_block, new_heading_and_content)

            # 5. 写回文件
            doc_path.write_text(modified_content, encoding='utf-8')
            
            success_msg = f"Successfully applied section change for heading: {target_heading_string}"
            logger.success(success_msg)
            self._send_completion_message(success_msg, "success", target_heading_string, file_path)
            
            return Message(content=success_msg, role=self.profile, send_to="ChangeCoordinator")
            
        except Exception as e:
            error_msg = f"Error in SectionApplier._act: {e}"
            logger.error(error_msg, exc_info=True)
            self._send_completion_message(error_msg, "failed", content_data.get("target_heading_string", "Unknown"), content_data.get("file_path", "Unknown"))
            return Message(content=error_msg, role=self.profile, send_to="ChangeCoordinator")
            
    def _get_line_number(self, content: str, pos: int) -> int:
        """Get the 1-based line number for a position in the content."""
        return content[:pos].count('\n') + 1
        
    def _send_completion_message(self, message: str, status: str, applied_heading: str, file_path: str):
        """Send a completion message to the environment."""
        completion_message = Message(
            content=json.dumps({
                "status": status,
                "message": message,
                "applied_heading": applied_heading,
                "file_path": file_path
            }),
            role=self.profile,
            send_to="ChangeCoordinator",
            cause_by="SectionApplicationCompleted"
        )
        self.rc.env.publish_message(completion_message)