
from metagpt.actions import Action
from metagpt_doc_writer.schemas.doc_structures import FullDraft, ReviewNotes, QAReport
from metagpt.schema import Message
from metagpt.logs import logger

# Define a global counter for demonstration purposes. In a real system, this would be managed by the ChiefPM role's state.
_revision_count = 0
MAX_REVISIONS = 2 # For testing, we'll limit to 2 revisions

class ReviewAndCommand(Action):
    async def run(self, draft: FullDraft, qa_report: QAReport = None) -> Message:
        global _revision_count

        # Simulate ContextOptimizer: For simplicity, we'll just use the full draft content.
        # In a real scenario, ContextOptimizer would summarize/extract relevant parts.
        document_summary = draft.content[:1000] + "..." if len(draft.content) > 1000 else draft.content

        review_prompt = f"""
        You are the Chief Product Manager. Your task is to review the provided document draft and decide if it's ready for approval or if it needs revisions.

        Document Draft (Summary/Snippet):
        ---
        {document_summary}
        ---

        {'QA Report: ' + qa_report.issues_found[0] if qa_report and qa_report.issues_found else ''}

        Current Revision Count: {_revision_count} / {MAX_REVISIONS}

        If the document needs revisions, provide detailed feedback in natural language. Focus on completeness, clarity, and adherence to the original goals.
        If the document is perfect and ready for final delivery, simply state "APPROVE".

        Example Revision Feedback:
        "The introduction needs to be more engaging. Please expand on the benefits section. Ensure all acceptance criteria are met."

        Example Approval:
        "APPROVE"
        """

        response = await self._aask(review_prompt)
        feedback = response.content

        if "APPROVE" in feedback.upper() or _revision_count >= MAX_REVISIONS:
            logger.info(f"Document approved after {_revision_count} revisions.")
            _revision_count = 0 # Reset for next project
            return Message(content="Document Approved", instruct_content=None) # Approval message
        else:
            _revision_count += 1
            logger.info(f"Document needs revision. Revision count: {_revision_count}")
            return Message(content="Document needs revision", instruct_content=ReviewNotes(feedback=feedback))
