# hierarchical/roles/archiver.py
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Type

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# -----------------

from metagpt.schema import Message
from metagpt.logs import logger
from hierarchical.roles.base_role import HierarchicalBaseRole
# --- 【核心修正】在这里同时导入 Outline 和 Section ---
from hierarchical.schemas import Outline, Section
from hierarchical.actions.complete_all_tasks import CompleteAllTasks

class Archiver(HierarchicalBaseRole):
    """
    Archiver Role.
    Assembles the final document from the completed Outline and saves it.
    """
    name: str = "Archiver"
    profile: str = "Archiver"
    goal: str = "Assemble and save the final document."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([])
        self._watch([CompleteAllTasks])
        
    async def _think(self) -> bool:
        """
        Overrides the default _think to make Archiver react to the completion signal.
        """
        if not self.rc.news:
            return False
        
        latest_msg = self.rc.news[-1]
        
        if latest_msg.content == "ALL_DOCUMENT_TASKS_COMPLETED":
            logger.debug(f"Archiver thinking: Found completion signal. TODO set to the message itself.")
            self.rc.todo = latest_msg
            return True
        
        logger.debug(f"Archiver thinking: Latest message is not the completion signal. No action needed.")
        return False

    def _assemble_document(self, outline: Outline) -> str:
        if not outline: return "# Error: Outline not found."
        content_parts = [f"# {outline.goal}"]
        
        # 这个函数的类型注解现在可以被正确识别了
        def recurse_assemble(sections: List[Section]):
            sorted_sections = sorted(sections, key=lambda s: s.display_id)
            for section in sorted_sections:
                title_prefix = '#' * section.level
                content_parts.append(f"{title_prefix} {section.display_id} {section.title}")
                if section.content:
                    content_parts.append(section.content)
                if section.sub_sections:
                    recurse_assemble(section.sub_sections)

        recurse_assemble(outline.root_sections)
        return "\n\n".join(content_parts)

    async def _act(self) -> Message:
        logger.info(f"--- {self.name} is acting... ---")
        
        if not isinstance(self.rc.todo, Message) or self.rc.todo.content != "ALL_DOCUMENT_TASKS_COMPLETED":
            logger.warning("Archiver activated but todo is not the correct completion signal. Skipping.")
            return None
            
        outline: Outline = self.context.outline
        final_doc_content = self._assemble_document(outline)

        output_path = Path("outputs") 
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_goal_name = "".join(c for c in outline.goal if c.isalnum() or c in " _-").strip()[:50]
        doc_filename = f"final_document_{safe_goal_name}_{timestamp}.md"
        doc_path = output_path / doc_filename
        doc_path.write_text(final_doc_content, encoding='utf-8')
        
        logger.success(f"最终文档已生成: {doc_path}")
        return Message(content=f"Document archived successfully: {doc_path}")