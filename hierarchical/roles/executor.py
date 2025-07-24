# hierarchical/roles/executor.py
import asyncio
import sys
from pathlib import Path
from typing import List, Tuple, Any

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
from hierarchical.actions import WriteSection, ReviewSection, ReviseSection
from hierarchical.utils import build_context_for_writing 

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
        self.set_actions([WriteSection(), ReviewSection(), ReviseSection()])
        self._watch(["hierarchical.roles.scheduler.Scheduler"])

    async def _think(self) -> bool:
        """
        Executor's thinking logic is simple: if a SectionBatch is received, process it.
        This avoids passing a huge history to the LLM, solving the context overflow issue.
        """
        if not self.rc.news:
            return False
        
        latest_msg = self.rc.news[-1]
        if isinstance(latest_msg.instruct_content, SectionBatch):
            logger.debug(f"Executor thinking: Found SectionBatch. Setting todo to PROCESS_BATCH.")
            self.rc.todo = "PROCESS_BATCH" 
            return True
            
        return False

    def _get_action(self, action_class: type) -> Action:
        """Helper to get an action instance by its class."""
        return next((a for a in self.actions if isinstance(a, action_class)), None)

    async def _process_section_workflow(self, section: Section) -> Tuple[str, str]:
        """Runs the real Write-Review-Revise workflow for a single section."""
        logger.info(f"  -> Starting REAL workflow for '{section.title}'...")
        
        semaphore = self.context.semaphore
        outline: Outline = self.context.outline
        
        async with semaphore:
            logger.success(f"   - Semaphore acquired for '{section.title}'.")
            
            write_action = self._get_action(WriteSection)
            review_action = self._get_action(ReviewSection)
            revise_action = self._get_action(ReviseSection)

            writing_context = build_context_for_writing(outline, section.section_id)

            # 1. Write
            draft = await self._execute_action(write_action, context=writing_context)
            final_content = draft

            # 2. Review
            review_context = {"target_section_title": section.title, "content": draft}
            review_result = await self._execute_action(review_action, context=review_context)
            logger.info(f"Review result for '{section.title}': {review_result}")

            # 3. Revise (if needed)
            if review_result == "NEEDS_REVISION":
                revise_context = {"target_section_title": section.title, "original_content": draft}
                final_content = await self._execute_action(
                    revise_action, 
                    context=revise_context, 
                    review_comments="Please improve clarity and add more examples."
                )

        logger.info(f"  <- Finished workflow for '{section.title}'.")
        return (section.section_id, final_content)

    async def _act(self) -> Message:
        """
        The main entry point for the Executor's action.
        Processes a batch of sections based on the signal from _think.
        """
        logger.info(f"--- {self.name} is acting... ---")
        
        if self.rc.todo != "PROCESS_BATCH":
            logger.warning("Executor was triggered but has no valid batch to process. Skipping.")
            return Message(content="No valid batch to process.")

        latest_msg = self.rc.news[-1]
        batch = latest_msg.instruct_content
        sections_to_process: List[Section] = batch.sections
        
        if not sections_to_process:
            logger.info("Executor received an empty batch. Nothing to do.")
            return Message(content="Completed empty batch.", role=self.profile, send_to="Scheduler")

        logger.info(f"Received {len(sections_to_process)} sections to process in parallel.")
        coroutines = [self._process_section_workflow(sec) for sec in sections_to_process]
        results = await asyncio.gather(*coroutines)
        
        outline: Outline = self.context.outline
        for section_id, final_content in results:
            target_section = outline.find_section(section_id)
            if target_section:
                target_section.content = final_content
                target_section.status = "COMPLETED"
        
        logger.success(f"Successfully processed {len(results)} sections.")
        return Message(content=f"Completed batch of {len(results)} sections.", role=self.profile, send_to="Scheduler")