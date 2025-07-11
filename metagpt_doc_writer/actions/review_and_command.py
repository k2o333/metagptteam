# 路径: /root/metagpt/mgfr/metagpt_doc_writer/actions/review_and_command.py

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt_doc_writer.schemas.doc_structures import FullDraft, ReviewNotes
from typing import ClassVar

REVIEW_PROMPT: ClassVar[str] = """
You are a meticulous Chief Product Manager. Review the following document draft and provide concise, actionable feedback.
Your feedback should be in natural language. If no changes are needed, respond with "No changes needed."

--- DOCUMENT DRAFT ---
{draft_content}
--- END OF DRAFT ---

Your review notes:
"""

class ReviewAndCommand(Action):
    """
    An action for a Chief PM to review a document and provide feedback.
    """
    async def run(self, full_draft: FullDraft) -> ReviewNotes:
        logger.info(f"Reviewing draft version {full_draft.version}...")
        
        prompt = REVIEW_PROMPT.format(draft_content=full_draft.content)
        feedback_text = await self._aask(prompt)
        
        logger.info(f"Generated feedback: {feedback_text}")
        
        return ReviewNotes(feedback=feedback_text)