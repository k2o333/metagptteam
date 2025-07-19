# hierarchical/roles/scheduler.py
import sys
from pathlib import Path
from typing import List

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# -----------------

from metagpt.schema import Message
from metagpt.logs import logger
from hierarchical.roles.base_role import HierarchicalBaseRole
from hierarchical.schemas import Outline, Section, SectionBatch
from hierarchical.roles.chief_pm import ChiefPM
# 【重要】为了让 Scheduler 能够创建子大纲，它需要拥有 CreateSubOutline 这个 Action
from hierarchical.actions.create_sub_outline import CreateSubOutline

class Scheduler(HierarchicalBaseRole):
    """
    Tactical Scheduler Role.
    Monitors the Outline's state and dispatches tasks or triggers sub-division.
    """
    name: str = "Scheduler"
    profile: str = "Task Scheduler"
    goal: str = "Manage the document generation lifecycle by dispatching tasks and deciding when to deepen sections."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Scheduler 现在拥有创建子大纲的能力
        self.set_actions([CreateSubOutline])
        # 监听来自 ChiefPM (初始计划) 和 Executor (任务完成) 的消息
        self._watch([ChiefPM, "hierarchical.roles.executor.Executor"]) 

    def _get_sections_by_status(self, status: str) -> List[Section]:
        if not hasattr(self.context, 'outline') or not self.context.outline: return []
        outline: Outline = self.context.outline
        found_sections = []
        def recurse_find(sections: List[Section]):
            for section in sections:
                if section.status == status: found_sections.append(section)
                if section.sub_sections: recurse_find(section.sub_sections)
        recurse_find(outline.root_sections)
        return found_sections

    async def _act(self) -> Message:
        logger.info(f"--- {self.name} is acting... ---")
        if not hasattr(self.context, 'outline') or not self.context.outline: return None
        outline: Outline = self.context.outline

        # 决策逻辑:
        # 1. 优先处理需要创建子大纲的章节
        sections_to_create_outline_for = self._get_sections_by_status("PENDING_SUBDIVIDE")
        if sections_to_create_outline_for:
            target_section = sections_to_create_outline_for[0]
            logger.info(f"Creating sub-outline for '{target_section.title}'...")
            
            create_outline_action = self.actions[0]
            sub_sections = await create_outline_action.run(parent_section=target_section, goal=outline.goal)
            
            target_section.sub_sections = sub_sections
            target_section.status = "COMPLETED" # 父章节细分完成，恢复为COMPLETED
            
            # 重新触发自己，以便在下一轮派发这些新的 PENDING_WRITE 任务
            logger.info(f"Sub-outline for '{target_section.title}' created. Re-triggering scheduler.")
            return Message(content="Sub-outline created, ready for next round.", role=self.profile, send_to="Scheduler")

        # 2. 其次，派发待写任务
        sections_to_write = self._get_sections_by_status("PENDING_WRITE")
        if sections_to_write:
            logger.info(f"Found {len(sections_to_write)} sections to write. Dispatching to Executor.")
            for sec in sections_to_write: sec.status = "WRITING"
            batch = SectionBatch(sections=sections_to_write)
            return Message(content=f"Dispatching batch of {len(sections_to_write)} sections.", instruct_content=batch, role=self.profile, send_to="Executor")

        # 3. 如果无事可做，检查是否有可以深化的章节
        hier_config = self.context.kwargs.get("custom_config", {}).get("hierarchical_doc_writer", {})
        max_depth = hier_config.get("max_depth", 3)
        
        all_completed = self._get_sections_by_status("COMPLETED")
        sorted_completed = sorted(all_completed, key=lambda s: (s.level, s.display_id))
        
        for section in sorted_completed:
            if not section.sub_sections and section.level < max_depth:
                logger.info(f"Found section '{section.title}' to subdivide. Setting status to PENDING_SUBDIVIDE.")
                section.status = "PENDING_SUBDIVIDE"
                # 重新触发自己，在下一轮处理这个 PENDING_SUBDIVIDE 任务
                return Message(content=f"Requesting sub-outline for '{section.title}'.", role=self.profile, send_to="Scheduler")
        
        # 4. 如果以上都无事可做，才真正结束
        logger.success("No more tasks to write or subdivide. Signaling process end.")
        return Message(content="ALL_TASKS_COMPLETED")