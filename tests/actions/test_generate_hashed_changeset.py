
import pytest
import hashlib
from unittest.mock import patch
from metagpt.provider.base_llm import BaseLLM
from metagpt_doc_writer.actions.generate_changeset import GenerateChangeSet
from metagpt_doc_writer.schemas.doc_structures import ReviewNotes, FullDraft, ValidatedChangeSet

def create_hashed_anchor(text: str) -> str:
    """Helper function to create a hashed anchor ID."""
    return hashlib.sha1(text.encode()).hexdigest()[:12]

@pytest.mark.asyncio
async def test_generate_changeset_with_hashed_anchors(mocker):
    """
    Tests that GenerateChangeSet can correctly identify and use hashed anchors.
    """
    # 1. Prepare the test data
    original_content = "This is the first paragraph."
    anchor_id = create_hashed_anchor(original_content)
    
    full_draft_content = f"[anchor-id::{anchor_id}]{original_content}"
    full_draft = FullDraft(content=full_draft_content, version=1)
    
    review_notes = ReviewNotes(feedback="Please change the first paragraph to something new.")
    
    # 2. Mock the LLM response
    new_content = "This is the updated paragraph."
    llm_response = f"""
    {{
      "changes": [
        {{
          "operation": "REPLACE_BLOCK",
          "anchor_id": "{anchor_id}",
          "new_content": "{new_content}",
          "comment": "Updated the first paragraph as requested."
        }}
      ]
    }}
    """
    mocker.patch('metagpt.provider.base_llm.BaseLLM.aask', return_value=llm_response)
    
    # 3. Run the action
    action = GenerateChangeSet()
    validated_changeset = await action.run(review_notes, full_draft)
    
    # 4. Assert the results
    assert isinstance(validated_changeset, ValidatedChangeSet)
    assert len(validated_changeset.changes) == 1
    change = validated_changeset.changes[0]
    assert change.operation == "REPLACE_BLOCK"
    assert change.anchor_id == anchor_id
    assert change.new_content == new_content
    BaseLLM.aask.assert_called_once()
