# hierarchical/roles/scheduler.py
import sys
from pathlib import Path

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# -----------------

from metagpt.schema import Message
from metagpt.logs import logger
from hierarchical.roles.base_role import HierarchicalBaseRole
# --- 导入 SectionBatch ---
from hierarchical.schemas import Outline, Section, SectionBatch
from typing import List

from hierarchical.roles.chief_pm import ChiefPM

class Scheduler(HierarchicalBaseRole):
    """
    Tactical Scheduler Role.
    Monitors the Outline's state and dispatches tasks.
    """
    name: str = "Scheduler"
    profile: str = "Task Scheduler"
    goal: str = "Manage the document generation lifecycle by dispatching tasks."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([])
        # 使用字符串来指定监听的 Role，避免循环导入
        self._watch([ChiefPM, "hierarchical.roles.executor.Executor"]) 

    def _get_sections_by_status(self, status: str) -> List[Section]:
        """Helper to find all sections with a specific status in the outline."""
        if not hasattr(self.context, 'outline') or not self.context.outline:
            return []
        outline: Outline = self.context.outline
        found_sections = []
        
        def recurse_find(sections: List[Section]):
            for section in sections:
                if section.status == status:
                    found_sections.append(section)
                if section.sub_sections:
                    recurse_find(section.sub_sections)

        recurse_find(outline.root_sections)
        return found_sections

    async def _act(self) -> Message:
        logger.info(f"--- {self.name} is acting... ---")
        if not hasattr(self.context, 'outline') or not self.context.outline:
            logger.warning("Outline not found in context, Scheduler cannot act.")
            return None

        # 决策逻辑:
        sections_to_write = self._get_sections_by_status("PENDING_WRITE")
        if sections_to_write:
            logger.info(f"Found {len(sections_to_write)} sections to write. Dispatching to Executor.")
            
            for sec in sections_to_write:
                sec.status = "WRITING" 

            # 将列表包装成 SectionBatch 对象
            batch = SectionBatch(sections=sections_to_write)
            
            return Message(
                content=f"Dispatching batch of {len(sections_to_write)} sections for writing.",
                instruct_content=batch,
                role=self.profile,
                send_to="Executor"
            )

        pending_tasks = (self._get_sections_by_status("PENDING_WRITE") or 
                         self._get_sections_by_status("WRITING") or 
                         self._get_sections_by_status("PENDING_SUBDIVIDE"))
                         
        if not pending_tasks:
            logger.success("All sections are COMPLETED. Signaling process end.")
            return Message(content="ALL_TASKS_COMPLETED")

        logger.info("Scheduler has no immediate tasks. Waiting for next trigger from Executor.")
        return None