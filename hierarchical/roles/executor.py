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

from metagpt.schema import Message
from metagpt.logs import logger
from hierarchical.roles.base_role import HierarchicalBaseRole
from hierarchical.schemas import Outline, Section, SectionBatch

class Executor(HierarchicalBaseRole):
    """
    Executor Role.
    Receives a batch of sections and processes them in parallel.
    """
    name: str = "Executor"
    profile: str = "Task Executor"
    goal: str = "Write, review, and revise document sections efficiently."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([])
        self._watch(["hierarchical.roles.scheduler.Scheduler"])

    async def _process_section_workflow(self, section: Section) -> Tuple[str, str]:
        """Mocks the Write-Review-Revise workflow for a single section."""
        logger.info(f"  -> Starting workflow for '{section.title}'...")
        await asyncio.sleep(1) # Simulate work
        final_content = f"## {section.display_id} {section.title}\n\nThis is the final, mocked content for this section."
        logger.info(f"  <- Finished workflow for '{section.title}'.")
        return (section.section_id, final_content)


    async def _act(self) -> Message:
        logger.info(f"--- {self.name} is acting... ---")
        
        # --- 【核心修正】采纳官方建议，从 self.rc.news 获取消息 ---
        if not self.rc.news:
             logger.warning("Executor was triggered but has no new messages in rc.news. Skipping.")
             return None
        
        # 通常，触发行动的是 news 列表中的最新消息
        latest_msg = self.rc.news[-1]
             
        # 解包 SectionBatch 对象
        batch = latest_msg.instruct_content
        if not isinstance(batch, SectionBatch):
            logger.warning(f"Executor received a message, but instruct_content is not a SectionBatch. Got {type(batch)}. Ignoring.")
            return None
            
        sections_to_process: List[Section] = batch.sections

        if not sections_to_process:
            logger.info("Executor received an empty batch of sections. Nothing to do.")
            return Message(
                content="Completed processing empty batch.",
                role=self.profile,
                send_to="Scheduler"
            )

        logger.info(f"Received {len(sections_to_process)} sections to process in parallel.")

        coroutines = [self._process_section_workflow(sec) for sec in sections_to_process]
        results = await asyncio.gather(*coroutines)

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

        # Notify the Scheduler that this batch is done
        return Message(
            content=f"Completed processing batch of {len(results)} sections.",
            role=self.profile,
            send_to="Scheduler"
        )