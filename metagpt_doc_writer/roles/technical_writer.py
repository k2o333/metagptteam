# 路径: /root/metagpt/mgfr/metagpt_doc_writer/roles/technical_writer.py (更新版)

from metagpt.logs import logger
from metagpt.schema import Message
from .base_role import MyBaseRole
from metagpt_doc_writer.actions.write_section import WriteSection
from metagpt_doc_writer.schemas.doc_structures import ApprovedTask, DraftSection

class TechnicalWriter(MyBaseRole):
    name: str = "TechnicalWriter"
    profile: str = "Technical Writer"
    goal: str = "Write high-quality, clear, and accurate technical documentation sections."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([WriteSection()])
        self._watch({ApprovedTask})

    async def _act(self) -> Message:
        """
        Takes an ApprovedTask and writes a DraftSection for it.
        """
        logger.info(f"Executing action: {self.name}")
        
        memories = self.get_memories()
        try:
            approved_task_msg = next(m for m in reversed(memories) if isinstance(m.instruct_content, ApprovedTask))
        except StopIteration:
            logger.warning("No ApprovedTask found in memory. Nothing to write.")
            return None

        write_action = self.actions[0]
        draft_section = await write_action.run(approved_task_msg.instruct_content)
        
        return Message(content=draft_section.content, instruct_content=draft_section)