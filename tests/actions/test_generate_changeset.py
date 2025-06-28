
import pytest
from metagpt_doc_writer.actions.generate_changeset import GenerateChangeSet
from metagpt_doc_writer.schemas.doc_structures import ReviewNotes, FullDraft

@pytest.mark.asyncio
async def test_changeset_generation():
    # No mocking needed for the dummy implementation
    action = GenerateChangeSet()
    review_notes = ReviewNotes(feedback="Make it more concise.")
    full_draft = FullDraft(content="[anchor-id::anc123]This is some long content.")
    changeset = await action.run(review_notes, full_draft)
    assert len(changeset.changes) == 1
    assert changeset.changes[0].operation == "REPLACE_BLOCK"
