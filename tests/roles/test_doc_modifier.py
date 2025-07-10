
import pytest
from unittest.mock import Mock
from metagpt_doc_writer.roles.doc_modifier import DocModifier
from metagpt_doc_writer.schemas.doc_structures import Change

@pytest.fixture
def modifier(mocker):
    """Provides a DocModifier instance with a mocked LLM."""
    mock_llm_instance = Mock()
    mock_llm_instance.system_prompt = ""
    mocker.patch('metagpt.context.Context.llm_with_cost_manager_from_llm_config', return_value=mock_llm_instance)
    return DocModifier()

def test_apply_replace_block(modifier):
    content = "[anchor-id::abc]Old content.[anchor-id::def]"
    changes = [Change(operation="REPLACE_BLOCK", anchor_id="abc", new_content="New content.", comment="Replace content")]
    new_content = modifier._apply_changes(content, changes)
    assert new_content == "[anchor-id::abc]New content.[anchor-id::def]"

def test_apply_insert_after(modifier):
    content = "[anchor-id::abc]First paragraph."
    changes = [Change(operation="INSERT_AFTER", anchor_id="abc", new_content="\n\n[anchor-id::ghi]Second paragraph.", comment="Insert new paragraph")]
    new_content = modifier._apply_changes(content, changes)
    assert new_content == "[anchor-id::abc]First paragraph.\n\n[anchor-id::ghi]Second paragraph."

def test_apply_delete_section(modifier):
    content = "[anchor-id::abc]This should be deleted.[anchor-id::def]This should remain."
    changes = [Change(operation="DELETE_SECTION", anchor_id="abc", comment="Delete obsolete section")]
    new_content = modifier._apply_changes(content, changes)
    assert new_content == "[anchor-id::def]This should remain."

def test_apply_multiple_changes(modifier):
    content = "[anchor-id::abc]Content A.[anchor-id::def]Content B."
    changes = [
        Change(operation="REPLACE_BLOCK", anchor_id="abc", new_content="New A.", comment="Update A"),
        Change(operation="INSERT_AFTER", anchor_id="def", new_content="\n[anchor-id::ghi]Content C.", comment="Add C")
    ]
    new_content = modifier._apply_changes(content, changes)
    assert new_content == "[anchor-id::abc]New A.[anchor-id::def]Content B.\n[anchor-id::ghi]Content C."

def test_apply_change_anchor_not_found(modifier):
    content = "[anchor-id::abc]Some content."
    changes = [Change(operation="REPLACE_BLOCK", anchor_id="xyz", new_content="New content.", comment="Anchor not found")]
    # The modifier should ideally log a warning and not change the content.
    new_content = modifier._apply_changes(content, changes)
    assert new_content == content

