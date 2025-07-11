# 路径: /root/metagpt/mgfr/metagpt_doc_writer/roles/qa_agent.py (新增文件)

from metagpt.logs import logger
from metagpt.schema import Message
from .base_role import MyBaseRole
from metagpt_doc_writer.actions.automated_check import AutomatedCheck
from metagpt_doc_writer.schemas.doc_structures import FullDraft, QAReport

class QAAgent(MyBaseRole):
    name: str = "QAAgent"
    profile: str = "Quality Assurance Agent"
    goal: str = "To ensure the quality and accuracy of the document through automated checks."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([AutomatedCheck()])
        self._watch({FullDraft})  # Triggered when a new full draft is ready

    async def _act(self) -> Message:
        """
        Performs a QA check on the latest document draft.
        """
        logger.info(f"Executing action: {self.name}")
        
        memories = self.get_memories()
        try:
            draft_msg = next(m for m in reversed(memories) if isinstance(m.instruct_content, FullDraft))
        except StopIteration:
            logger.warning("No FullDraft found in memory for QA check. Nothing to do.")
            return None

        check_action = self.actions[0]
        qa_report = await check_action.run(draft_msg.instruct_content)
        
        return Message(content=qa_report.model_dump_json(indent=2), instruct_content=qa_report)