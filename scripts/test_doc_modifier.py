
from unittest.mock import Mock
from metagpt_doc_writer.roles.doc_modifier import DocModifier
from metagpt_doc_writer.schemas.doc_structures import ValidatedChangeSet, FullDraft, Change
from metagpt.schema import Message

def test_doc_modifier_apply_changes():
    modifier = DocModifier()
    content = "[anchor-id::abc]Old content.[anchor-id::def]"
    changes = [Change(operation="REPLACE_BLOCK", anchor_id="abc", new_content="New content.", comment="...")]
    
    new_content = modifier._apply_changes(content, changes)
    print("Original content:", content)
    print("Content after changes:", new_content)
    
    assert "[anchor-id::abc]New content." in new_content
    assert "[anchor-id::def]" in new_content

def test_doc_modifier_act(mocker):
    # Mock the LLM creation to prevent actual LLM initialization errors
    mock_llm_instance = Mock()
    mock_llm_instance.system_prompt = ""
    mocker.patch('metagpt.context.Context.llm_with_cost_manager_from_llm_config', return_value=mock_llm_instance)

    modifier = DocModifier()

    # Prepare mock messages for the modifier's memory
    original_content = "[anchor-id::chap1]Chapter 1 content.[anchor-id::chap2]Chapter 2 content."
    original_draft = FullDraft(content=original_content)
    modifier.rc.memory.add(Message(content="Original Draft", instruct_content=original_draft))

    changes = [
        Change(operation="REPLACE_BLOCK", anchor_id="chap1", new_content="Updated Chapter 1 content.", comment="Update chap1"),
        Change(operation="INSERT_AFTER", anchor_id="chap2", new_content="\n[anchor-id::new_chap]New Chapter content.", comment="Add new chap")
    ]
    validated_changeset = ValidatedChangeSet(changes=changes)
    modifier.rc.memory.add(Message(content="Validated Changeset", instruct_content=validated_changeset))

    # Simulate receiving news (this is usually handled by the Team/Environment)
    modifier.rc.news = [Message(content="Trigger act", instruct_content=validated_changeset)]

    # Call the _act method
    import asyncio
    modified_message = asyncio.run(modifier._act())

    # Assertions
    assert modified_message is not None
    assert isinstance(modified_message.instruct_content, FullDraft)
    modified_draft = modified_message.instruct_content
    print("\nModified Draft Content:")
    print(modified_draft.content)

    assert "Updated Chapter 1 content." in modified_draft.content
    assert "New Chapter content." in modified_draft.content
    assert "[anchor-id::chap1]Updated Chapter 1 content." in modified_draft.content
    assert "[anchor-id::chap2]Chapter 2 content.\n[anchor-id::new_chap]New Chapter content." in modified_draft.content

if __name__ == "__main__":
    test_doc_modifier_apply_changes()
    # To run test_doc_modifier_act, you need to pass mocker fixture, which is typically done by pytest.
    # For standalone execution, you might need a dummy mocker or run it via pytest.
    # For now, we'll just run the apply_changes test.
