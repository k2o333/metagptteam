import pytest
import json
from metagpt.provider.base_llm import BaseLLM
from metagpt_doc_writer.actions.generate_changeset import GenerateChangeSet
from metagpt_doc_writer.schemas.doc_structures import ReviewNotes, FullDraft, ValidatedChangeSet, Change

@pytest.mark.asyncio
async def test_changeset_repair_loop(mocker):
    # First, mock the LLM to return a malformed JSON
    # Then, on the second call, return a valid JSON
    mock_llm_calls = [
        '{"changes": [ ... malformed ...',  # First call returns malformed JSON
        '{"changes": [{"operation": "REPLACE_BLOCK", "anchor_id": "anc123", "new_content": "New content.", "comment": "Fixed content"}]}'  # Second call returns valid JSON
    ]
    mocker.patch('metagpt.provider.base_llm.BaseLLM.aask', side_effect=mock_llm_calls)

    action = GenerateChangeSet()
    review_notes = ReviewNotes(feedback="Please fix this.")
    full_draft = FullDraft(content="[anchor-id::anc123]Old content.", version=1)
    
    # Mock the _validate_anchors method to avoid complex validation logic in this test
    mocker.patch.object(action, '_validate_anchors', return_value=True)

    validated_changeset = await action.run(review_notes, full_draft)

    assert isinstance(validated_changeset, ValidatedChangeSet)
    assert len(validated_changeset.changes) == 1
    assert validated_changeset.changes[0].operation == "REPLACE_BLOCK"
    # Ensure that aask was called twice (initial attempt + repair attempt)
    assert BaseLLM.aask.call_count == 2
