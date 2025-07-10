from metagpt.actions import Action
from metagpt.logs import logger
from metagpt_doc_writer.schemas.doc_structures import ReviewNotes, FullDraft, ValidatedChangeSet

class GenerateChangeSet(Action):
    """A placeholder Action for generating changesets."""
    async def run(self, review_notes: ReviewNotes, full_draft: FullDraft) -> ValidatedChangeSet:
        logger.warning("Running a legacy Action: GenerateChangeSet.")
        return ValidatedChangeSet(changes=[])