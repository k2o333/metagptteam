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
from hierarchical.actions import CreateSubOutline, CompleteAllTasks

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
        self.set_actions([CreateSubOutline(), CompleteAllTasks()])
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

    async def _think(self) -> bool:
        """
        Overrides the default _think to decide precisely what the todo is,
        based on the current state of the Outline.
        """
        self.rc.todo = None

        if self._get_sections_by_status("PENDING_WRITE"):
            self.rc.todo = "DISPATCH_WRITE_TASKS"
            logger.debug(f"Scheduler thinking: Found PENDING_WRITE sections. TODO set to: {self.rc.todo}")
            return True

        if self._get_sections_by_status("PENDING_SUBDIVIDE"):
            self.rc.todo = self.actions[0] # Assumes CreateSubOutline is the first action
            logger.debug(f"Scheduler thinking: Found PENDING_SUBDIVIDE sections. TODO set to: {self.rc.todo.name}")
            return True

        # 从 custom_config 获取配置
        custom_config = self.context.kwargs.get("custom_config", {})
        hier_config = custom_config.get("hierarchical_doc_writer", {})
        max_depth = hier_config.get("max_depth", 3)
        
        all_completed = self._get_sections_by_status("COMPLETED")
        sorted_completed = sorted(all_completed, key=lambda s: (s.level, s.display_id))
        for section in sorted_completed:
            if not section.sub_sections and section.level < max_depth:
                section.status = "PENDING_SUBDIVIDE"
                self.rc.todo = "MARK_SUBDIVIDE_DONE" 
                logger.debug(f"Scheduler thinking: Found a COMPLETED section to deepen. TODO set to: {self.rc.todo}")
                return True

        if self.rc.news:
            self.rc.todo = self.actions[1] # Assumes CompleteAllTasks is the second action
            logger.debug(f"Scheduler thinking: No other tasks found. TODO set to: {self.rc.todo.name}")
            return True

        logger.debug("Scheduler thinking: No news and no pending tasks. Nothing to do.")
        return False

    async def _act(self) -> Message:
        logger.info(f"--- {self.name} is acting with todo: '{self.rc.todo}' ---")
        if not self.rc.todo:
            return Message(content="No task to do.")

        outline: Outline = self.context.outline

        if self.rc.todo == "DISPATCH_WRITE_TASKS":
            sections_to_write = self._get_sections_by_status("PENDING_WRITE")
            logger.info(f"Dispatching {len(sections_to_write)} sections to Executor.")
            for sec in sections_to_write: sec.status = "WRITING"
            batch = SectionBatch(sections=sections_to_write)
            return Message(content="Dispatching sections for writing.", instruct_content=batch, role=self.profile, send_to="Executor")

        elif self.rc.todo == "MARK_SUBDIVIDE_DONE":
            return Message(content="Section marked for subdivision, re-triggering.", role=self.profile, send_to="Scheduler")

        elif isinstance(self.rc.todo, CreateSubOutline):
            sections_to_subdivide = self._get_sections_by_status("PENDING_SUBDIVIDE")
            if not sections_to_subdivide: 
                return Message(content="No sections to subdivide.")
            
            target_section = sections_to_subdivide[0]
            logger.info(f"Creating sub-outline for '{target_section.title}'...")
            
            # 【核心修改】使用我们新的执行器
            sub_sections = await self._execute_action(
                self.rc.todo,
                parent_section=target_section,
                goal=outline.goal
            )
            
            target_section.sub_sections = sub_sections
            target_section.status = "COMPLETED"
            return Message(content="Sub-outline created.", role=self.profile, send_to="Scheduler")

        elif isinstance(self.rc.todo, CompleteAllTasks):
            # CompleteAllTasks 不调用LLM，直接 run 即可
            result = await self.rc.todo.run()
            logger.success(f"Signaling process end: {result}")
            return Message(content=result, role=self.profile, send_to="Archiver")
        
        return Message(content="Unknown task, idling.")