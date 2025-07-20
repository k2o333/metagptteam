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
from hierarchical.actions.create_sub_outline import CreateSubOutline
from hierarchical.actions.complete_all_tasks import CompleteAllTasks

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
        # This helper function remains the same
        if not hasattr(self.context, 'outline') or not self.context.outline: return []
        outline: Outline = self.context.outline
        found_sections = []
        def recurse_find(sections: List[Section]):
            for section in sections:
                if section.status == status: found_sections.append(section)
                if section.sub_sections: recurse_find(section.sub_sections)
        recurse_find(outline.root_sections)
        return found_sections

    # --- 【核心修正】实现一个强大的 _think 方法 ---
    async def _think(self) -> bool:
        """
        Overrides the default _think to decide precisely what the todo is,
        based on the current state of the Outline.
        """
        # 默认情况下，无事可做
        self.rc.todo = None

        # 决策树:
        # 1. 最高优先级：派发待写任务
        if self._get_sections_by_status("PENDING_WRITE"):
            # 定义一个“虚拟”的待办事项信号，让 _act 知道要派发任务
            self.rc.todo = "DISPATCH_WRITE_TASKS"
            logger.debug(f"Scheduler thinking: Found PENDING_WRITE sections. TODO set to: {self.rc.todo}")
            return True

        # 2. 次高优先级：为待深化章节创建子大纲
        if self._get_sections_by_status("PENDING_SUBDIVIDE"):
            # 设置待办事项为 CreateSubOutline 这个 Action
            self.rc.todo = self.actions[0] # Assumes CreateSubOutline is the first action
            logger.debug(f"Scheduler thinking: Found PENDING_SUBDIVIDE sections. TODO set to: {self.rc.todo.name}")
            return True

        # 3. 再次，检查是否有可以标记为“待深化”的章节
        hier_config = self.context.kwargs.get("custom_config", {}).get("hierarchical_doc_writer", {})
        max_depth = hier_config.get("max_depth", 3)
        all_completed = self._get_sections_by_status("COMPLETED")
        sorted_completed = sorted(all_completed, key=lambda s: (s.level, s.display_id))
        for section in sorted_completed:
            if not section.sub_sections and section.level < max_depth:
                section.status = "PENDING_SUBDIVIDE"
                # 定义一个“虚拟”的待办事项，让 _act 知道要去深化
                self.rc.todo = "MARK_SUBDIVIDE_DONE" 
                logger.debug(f"Scheduler thinking: Found a COMPLETED section to deepen. TODO set to: {self.rc.todo}")
                return True

        # 4. 如果以上都无事可做，且有新消息触发（意味着一个循环刚结束）
        #    那么就认为是所有任务都完成了
        if self.rc.news:
            self.rc.todo = self.actions[1] # Assumes CompleteAllTasks is the second action
            logger.debug(f"Scheduler thinking: No other tasks found. TODO set to: {self.rc.todo.name}")
            return True

        # 如果连新消息都没有，那就是真的无事可做
        logger.debug("Scheduler thinking: No news and no pending tasks. Nothing to do.")
        return False

    # --- 【核心修正】简化 _act 方法，使其只负责执行 ---
    async def _act(self) -> Message:
        logger.info(f"--- {self.name} is acting with todo: '{self.rc.todo}' ---")
        if not self.rc.todo:
            return None # Should not happen if _think is correct

        outline: Outline = self.context.outline

        # 根据 _think 设置的 todo 来执行，不再做决策
        if self.rc.todo == "DISPATCH_WRITE_TASKS":
            sections_to_write = self._get_sections_by_status("PENDING_WRITE")
            logger.info(f"Dispatching {len(sections_to_write)} sections to Executor.")
            for sec in sections_to_write: sec.status = "WRITING"
            batch = SectionBatch(sections=sections_to_write)
            return Message(content="Dispatching sections for writing.", instruct_content=batch, role=self.profile, send_to="Executor")

        elif self.rc.todo == "MARK_SUBDIVIDE_DONE":
            # 刚刚在 _think 中标记了一个章节为 PENDING_SUBDIVIDE，
            # 现在发个消息重新触发自己，以便下一轮的 _think 能看到 PENDING_SUBDIVIDE 状态。
            return Message(content="Section marked for subdivision, re-triggering.", role=self.profile, send_to="Scheduler")

        elif isinstance(self.rc.todo, CreateSubOutline):
            sections_to_subdivide = self._get_sections_by_status("PENDING_SUBDIVIDE")
            if not sections_to_subdivide: return None
            
            target_section = sections_to_subdivide[0]
            logger.info(f"Creating sub-outline for '{target_section.title}'...")
            sub_sections = await self.rc.todo.run(parent_section=target_section, goal=outline.goal)
            target_section.sub_sections = sub_sections
            target_section.status = "COMPLETED"
            return Message(content="Sub-outline created.", role=self.profile, send_to="Scheduler")

        elif isinstance(self.rc.todo, CompleteAllTasks):
            result = await self.rc.todo.run()
            logger.success(f"Signaling process end: {result}")
            return Message(content=result, role=self.profile, send_to="Archiver")
        
        return None