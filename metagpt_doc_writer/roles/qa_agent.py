# /root/metagpt/mgfr/metagpt_doc_writer/roles/qa_agent.py (原生重构版)

from .base_role import DocWriterBaseRole
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt_doc_writer.actions.automated_check import AutomatedCheck
from metagpt_doc_writer.schemas.doc_structures import FullDraft, QAReport

class QAAgent(DocWriterBaseRole): # 【关键修正】: 继承自 Role
    name: str = "QAAgent"
    profile: str = "Quality Assurance Agent"
    goal: str = "To ensure the quality and accuracy of the document through automated checks."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([AutomatedCheck])
        self._watch({FullDraft})

    async def _act(self) -> Message:
        logger.info(f"Executing action: {self.name}")
        
        draft_msg = self.rc.history[-1]
        
        qa_report = await self.rc.todo.run(draft_msg.instruct_content)
        
        return Message(content=qa_report.model_dump_json(indent=2), instruct_content=qa_report, cause_by=type(self.rc.todo))