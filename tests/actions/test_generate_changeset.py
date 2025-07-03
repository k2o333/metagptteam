
import pytest
import json
import os
from unittest.mock import AsyncMock, MagicMock

# Set logging level to DEBUG for more verbose output
import logging
logging.basicConfig(level=logging.DEBUG)

# Set a dummy key to bypass the config check during initialization
os.environ["OPENAI_API_KEY"] = "sk-dummy"

# Mock metagpt.config2.config before importing anything that might use it
@pytest.fixture(autouse=True)
def mock_metagpt_config(mocker):
    # Attempt to clean up problematic environment variables for testing
    original_shell = os.environ.pop('SHELL', None)
    
    mock_llm_config = MagicMock()
    mock_llm_config.api_key = "sk-dummy-key"
    mock_llm_config.api_type = "openai"
    mock_llm_config.model = "gpt-4o-mini"
    mock_llm_config.base_url = "https://api.openai.com/v1"
    
    mock_config_instance = MagicMock()
    mock_config_instance.llm = mock_llm_config
    
    mocker.patch('metagpt.config2.config', new=mock_config_instance)

    # Restore environment variable after test
    if original_shell is not None:
        os.environ['SHELL'] = original_shell

from metagpt.provider.base_llm import BaseLLM
from metagpt_doc_writer.actions.generate_changeset import GenerateChangeSet, AnchorNotFoundException
from metagpt_doc_writer.schemas.doc_structures import ReviewNotes, FullDraft, ValidatedChangeSet

@pytest.fixture
def mock_llm():
    return AsyncMock(spec=BaseLLM)

@pytest.mark.asyncio
async def test_run_success_first_try(mock_llm):
    # Arrange
    correct_json_str = '{"changes": [{"operation": "REPLACE_BLOCK", "anchor_id": "anc123", "new_content": "New.", "comment": "Test"}]}'
    mock_llm.aask.return_value = correct_json_str
    
    action = GenerateChangeSet(llm=mock_llm)
    review_notes = ReviewNotes(feedback="Make it short.")
    full_draft = FullDraft(content="[anchor-id::anc123]This is some long content.")

    # Act
    result = await action.run(review_notes, full_draft)

    # Assert
    assert isinstance(result, ValidatedChangeSet)
    assert len(result.changes) == 1
    assert result.changes[0].anchor_id == "anc123"
    mock_llm.aask.assert_called_once()

@pytest.mark.asyncio
async def test_run_repairs_malformed_json(mock_llm):
    # Arrange
    malformed_json_str = '{"changes": [{"operation": "REPLACE_BLOCK", "anchor_id": "anc123", "new_content": "New.", "comment": "Test"}' # Missing closing brace
    correct_json_str = '{"changes": [{"operation": "REPLACE_BLOCK", "anchor_id": "anc123", "new_content": "New.", "comment": "Test"}]}'
    mock_llm.aask.side_effect = [malformed_json_str, correct_json_str]
    
    action = GenerateChangeSet(llm=mock_llm)
    review_notes = ReviewNotes(feedback="Make it short.")
    full_draft = FullDraft(content="[anchor-id::anc123]This is some long content.")

    # Act
    result = await action.run(review_notes, full_draft)

    # Assert
    assert mock_llm.aask.call_count == 2
    assert "The previous JSON generation failed" in mock_llm.aask.call_args_list[1].args[0]
    assert len(result.changes) == 1

@pytest.mark.asyncio
async def test_run_handles_anchor_not_found(mock_llm):
    # Arrange
    json_with_bad_anchor = '{"changes": [{"operation": "REPLACE_BLOCK", "anchor_id": "anc_bad", "new_content": "New.", "comment": "Test"}]}'
    json_with_good_anchor = '{"changes": [{"operation": "REPLACE_BLOCK", "anchor_id": "anc_good", "new_content": "New.", "comment": "Test"}]}'
    mock_llm.aask.side_effect = [json_with_bad_anchor, json_with_good_anchor]
    
    action = GenerateChangeSet(llm=mock_llm)
    review_notes = ReviewNotes(feedback="Make it short.")
    full_draft = FullDraft(content="[anchor-id::anc_good]This is some long content.")

    # Act
    result = await action.run(review_notes, full_draft)

    # Assert
    assert mock_llm.aask.call_count == 2
    assert "Previous Error**: An anchor you provided" in mock_llm.aask.call_args_list[1].args[0]
    assert len(result.changes) == 1
    assert result.changes[0].anchor_id == "anc_good"

@pytest.mark.asyncio
async def test_run_fails_after_max_retries(mock_llm):
    # Arrange
    malformed_json_str = '{"changes": [{"operation": "REPLACE_BLOCK"}]}' # Persistently bad
    mock_llm.aask.return_value = malformed_json_str
    
    action = GenerateChangeSet(llm=mock_llm)
    review_notes = ReviewNotes(feedback="Make it short.")
    full_draft = FullDraft(content="[anchor-id::anc123]This is some long content.")

    # Act
    result = await action.run(review_notes, full_draft)

    # Assert
    assert mock_llm.aask.call_count == 3
    assert len(result.changes) == 0 # Returns empty changeset on total failure
