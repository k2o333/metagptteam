from metagpt.actions import Action
from metagpt.logs import logger
from metagpt_doc_writer.schemas.doc_structures import FullDraft, ReviewNotes

class ReviewAndCommand(Action):
    """A placeholder Action for reviewing and commanding."""
    async def run(self, full_draft: FullDraft) -> ReviewNotes:
        logger.warning("Running a legacy Action: ReviewAndCommand.")
        return ReviewNotes(feedback="This is a placeholder review.")