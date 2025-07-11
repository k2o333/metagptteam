# 路径: /root/metagpt/mgfr/metagpt_doc_writer/actions/review_and_command.py (QA整合版)

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt_doc_writer.schemas.doc_structures import FullDraft, ReviewNotes, QAReport
from typing import ClassVar, Optional

# FIX: Updated prompt to include the QA Report as context.
REVIEW_PROMPT_WITH_QA: ClassVar[str] = """
You are a meticulous Chief Product Manager. Your task is to review the following document draft.
You have been provided with a QA report from your team. Use this report as a primary reference to guide your feedback.

**QA REPORT:**
---
{qa_report_content}
---

**DOCUMENT DRAFT:**
---
{draft_content}
---

**Instructions:**
Based on BOTH the QA report and your own assessment of the draft, provide concise, actionable feedback.
If no changes are needed, respond with "No changes needed."

Your comprehensive review notes:
"""

class ReviewAndCommand(Action):
    """
    An action for a Chief PM to review a document, considering a QA report, and provide feedback.
    """
    # FIX: Updated the run signature to accept an optional QAReport
    async def run(self, full_draft: FullDraft, qa_report: Optional[QAReport] = None) -> ReviewNotes:
        logger.info(f"Reviewing draft version {full_draft.version}...")
        
        qa_feedback_str = "No QA report provided."
        if qa_report:
            feedbacks = qa_report.feedbacks
            if feedbacks:
                qa_feedback_str = "\n".join(
                    f"- TYPE: {fb.feedback_type}, DESC: {fb.description}, SUGGESTION: {fb.suggestion}" 
                    for fb in feedbacks
                )
            else:
                qa_feedback_str = "No issues found by QA Agent."

        prompt = REVIEW_PROMPT_WITH_QA.format(
            qa_report_content=qa_feedback_str,
            draft_content=full_draft.content
        )
        feedback_text = await self._aask(prompt)
        
        logger.info(f"Generated feedback: {feedback_text}")
        
        return ReviewNotes(feedback=feedback_text)