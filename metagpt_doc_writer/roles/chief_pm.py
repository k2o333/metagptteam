# 路径: /root/metagpt/mgfr/metagpt_doc_writer/roles/chief_pm.py (QA整合版)

from metagpt.schema import Message
from metagpt.logs import logger

from metagpt_doc_writer.actions.review_and_command import ReviewAndCommand
from metagpt_doc_writer.schemas.doc_structures import FullDraft, ReviewNotes, QAReport
from .base_role import MyBaseRole

class ChiefPM(MyBaseRole):
    name: str = "ChiefPM"
    profile: str = "Chief Product Manager"
    goal: str = "Oversee the entire document generation process and ensure final quality."
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([ReviewAndCommand()])
        # FIX: Watch for both FullDraft and QAReport.
        # The logic in _act will handle waiting for both.
        self._watch({FullDraft, QAReport})

    async def _act(self) -> Message:
        """
        Reviews the latest FullDraft, now considering the QAReport.
        It waits until it has both a draft and its corresponding QA report.
        """
        logger.info(f"Executing action: {self.name} for reviewing.")
        
        memories = self.get_memories()
        try:
            # Find the latest draft and qa report
            # Note: This simple logic assumes one draft corresponds to one QA report.
            # A more robust implementation might match them by a shared ID.
            full_draft_msg = next(m for m in reversed(memories) if isinstance(m.instruct_content, FullDraft))
            qa_report_msg = next(m for m in reversed(memories) if isinstance(m.instruct_content, QAReport))
        except StopIteration:
            logger.info("Waiting for both FullDraft and QAReport to be available.")
            return None

        review_action = self.actions[0]
        if not isinstance(review_action, ReviewAndCommand):
            logger.error(f"Action setup error: Expected ReviewAndCommand, found {type(review_action)}.")
            return None
            
        # Pass both the draft and the report to the action
        review_notes = await review_action.run(
            full_draft=full_draft_msg.instruct_content,
            qa_report=qa_report_msg.instruct_content
        )
        
        return Message(content="Review notes generated based on draft and QA report.", instruct_content=review_notes)