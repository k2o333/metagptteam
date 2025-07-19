
# hierarchical/roles/executor.py
import asyncio
import sys
from pathlib import Path
from typing import List, Tuple

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# -----------------

from metagpt.actions import Action
from metagpt.schema import Message
from metagpt.logs import logger
from hierarchical.roles.base_role import HierarchicalBaseRole
from hierarchical.schemas import Outline, Section, SectionBatch
from hierarchical.actions.write_section import WriteSection

class Executor(HierarchicalBaseRole):
    """
    Executor Role.
    Receives a batch of sections and processes them in parallel using real Actions.
    """
    name: str = "Executor"
    profile: str = "Task Executor"
    goal: str = "Write, review, and revise document sections efficiently."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([WriteSection()])
        self._watch(["hierarchical.roles.scheduler.Scheduler"])

    def _get_action(self, action_class: type) -> Action:
        return next((a for a in self.actions if isinstance(a, action_class)), None)

    async def _process_section_workflow(self, section: Section) -> Tuple[str, str]:
        logger.info(f"  -> Starting REAL workflow for '{section.title}'...")
        
        semaphore = self.context.semaphore
        outline: Outline = self.context.outline
        
        async with semaphore:
            logger.success(f"   - Semaphore acquired for '{section.title}'. Starting LLM call.")
            
            write_action = self._get_action(WriteSection)
            if not write_action:
                logger.error("WriteSection action not found!")
                return (section.section_id, "Error: WriteSection action not found.")
            
            draft = await write_action.run(section=section, goal=outline.goal)
            final_content = f"## {section.display_id} {section.title}\n\n{draft}"

        logger.info(f"  <- Finished workflow for '{section.title}'. Semaphore released.")
        return (section.section_id, final_content)

    async def _act(self) -> Message:
        logger.info(f"--- {self.name} is acting... ---")
        
        if not self.rc.news:
             logger.warning("Executor has no new messages. Skipping.")
             return None
             
        latest_msg = self.rc.news[-1]
        batch = latest_msg.instruct_content
        if not isinstance(batch, SectionBatch):
            logger.warning(f"Executor received non-SectionBatch message. Ignoring.")
            return None
            
        sections_to_process: List[Section] = batch.sections
        if not sections_to_process:
            logger.info("Executor received an empty batch. Nothing to do.")
            return Message(content="Completed empty batch.", role=self.profile, send_to="Scheduler")

        logger.info(f"Received {len(sections_to_process)} sections to process in parallel.")
        coroutines = [self._process_section_workflow(sec) for sec in sections_to_process]
        results = await asyncio.gather(*coroutines)

        # --- 【核心修正】在使用 outline 前，先从 context 中获取它 ---
        if not hasattr(self.context, 'outline') or not self.context.outline:
             logger.error("Outline not found in context. Cannot update results.")
             return None
        outline: Outline = self.context.outline

        for section_id, final_content in results:
            target_section = outline.find_section(section_id)
            if target_section:
                target_section.content = final_content
                target_section.status = "COMPLETED"
        
        logger.success(f"Successfully processed {len(results)} sections.")
        return Message(content=f"Completed batch of {len(results)} sections.", role=self.profile, send_to="Scheduler")