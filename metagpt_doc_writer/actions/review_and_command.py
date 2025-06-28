
from metagpt.actions import Action
from metagpt_doc_writer.schemas.doc_structures import FullDraft, ReviewNotes

class ReviewAndCommand(Action):
    async def run(self, draft: FullDraft) -> ReviewNotes:
        # In a real implementation, this would use an LLM to review the draft and provide feedback.
        # For now, we'll just create dummy review notes.
        return ReviewNotes(feedback="This is a dummy review. Please make the content more concise.")
