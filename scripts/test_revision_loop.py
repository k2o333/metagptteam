
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from metagpt.schema import Message
from metagpt.context import Context
from metagpt.roles.role import RoleContext
from metagpt_doc_writer.roles.chief_pm import ChiefPM
from metagpt_doc_writer.roles.changeset_generator import ChangeSetGenerator
from metagpt_doc_writer.roles.doc_modifier import DocModifier
from metagpt_doc_writer.schemas.doc_structures import FullDraft, ReviewNotes, ValidatedChangeSet, Change, QAReport

async def main():
    # Mock the LLM creation to prevent actual LLM initialization errors
    mock_llm_instance = Mock()
    mock_llm_instance.system_prompt = ""
    # Mock _aask method for actions with AsyncMock
    mock_llm_instance.aask = AsyncMock(side_effect=[
        # ChiefPM's first review: needs revision
        Mock(content="The introduction needs to be more concise. Please rephrase the first paragraph."),
        # ChangeSetGenerator's first attempt: valid JSON
        Mock(content='''
        {
            "changes": [
                {
                    "operation": "REPLACE_BLOCK",
                    "anchor_id": "anc123",
                    "new_content": "This is the revised, concise introduction.",
                    "comment": "Rephrased for conciseness."
                }
            ]
        }
        '''),
        # ChiefPM's second review: approves
        Mock(content="APPROVE")
    ])
    # Mock parse_json method for LLM
    mock_llm_instance.parse_json = Mock(side_effect=[
        # ChangeSetGenerator's parse_json
        {
            "changes": [
                {
                    "operation": "REPLACE_BLOCK",
                    "anchor_id": "anc123",
                    "new_content": "This is the revised, concise introduction.",
                    "comment": "Rephrased for conciseness."
                }
            ]
        }
    ])

    # Patch the llm_with_cost_manager_from_llm_config method in Context
    mocker_patch = patch('metagpt.context.Context.llm_with_cost_manager_from_llm_config', return_value=mock_llm_instance)
    mocker_patch.start() # Start the patch

    # Create a mock RoleContext and add the initial message to its memory
    mock_rc_memory = Mock()
    draft_content = "[anchor-id::anc123]This is the original content that needs to be made more concise."
    initial_draft = FullDraft(content=draft_content)
    mock_rc_memory.get_by_class.side_effect = [
        [Message(content="", instruct_content=initial_draft)], # For ChiefPM to get FullDraft
        [Message(content="", instruct_content=ReviewNotes(feedback="dummy"))], # For ChangeSetGenerator to get ReviewNotes
        [Message(content="", instruct_content=initial_draft)], # For ChangeSetGenerator to get FullDraft
        [Message(content="", instruct_content=initial_draft)], # For DocModifier to get FullDraft
        [Message(content="", instruct_content=QAReport(issues_found=[]))], # For ChiefPM to get QAReport (optional)
        [Message(content="", instruct_content=initial_draft)], # For ChiefPM to get FullDraft again
    ]

    # Create instances of the roles
    chief_pm = ChiefPM()
    changeset_generator = ChangeSetGenerator()
    doc_modifier = DocModifier()

    # Manually set the mocked RoleContext memory for each role
    chief_pm.rc.memory = mock_rc_memory
    changeset_generator.rc.memory = mock_rc_memory
    doc_modifier.rc.memory = mock_rc_memory

    print("--- Starting Revision Loop ---")

    # First Revision Cycle
    review_notes_msg = await chief_pm._act()
    print("ChiefPM Review Notes:", review_notes_msg.instruct_content.feedback)
    mock_rc_memory.get_by_class.return_value = [review_notes_msg] # Update memory for ChangeSetGenerator

    changeset_msg = await changeset_generator._act()
    print("ChangeSet Generated:", changeset_msg.instruct_content.changes)
    
    # Simulate DocModifier applying changes
    # We need to get the latest FullDraft from memory for DocModifier
    current_draft_for_modifier = mock_rc_memory.get_by_class(FullDraft)[0].instruct_content.content
    modified_content = doc_modifier._apply_changes(current_draft_for_modifier, changeset_msg.instruct_content.changes)
    new_draft_after_mod = FullDraft(content=modified_content)
    print("Draft after modification:", new_draft_after_mod.content)
    
    # Mock the LLM creation to prevent actual LLM initialization errors
    mock_llm_instance = Mock()
    mock_llm_instance.system_prompt = ""
    # Mock _aask method for actions with AsyncMock
    mock_llm_instance.aask = AsyncMock(side_effect=[
        # ChiefPM's first review: needs revision
        Mock(content="The introduction needs to be more concise. Please rephrase the first paragraph."),
        # ChangeSetGenerator's first attempt: valid JSON
        Mock(content='''
        {
            "changes": [
                {
                    "operation": "REPLACE_BLOCK",
                    "anchor_id": "anc123",
                    "new_content": "This is the revised, concise introduction.",
                    "comment": "Rephrased for conciseness."
                }
            ]
        }
        '''),
        # ChiefPM's second review: approves
        Mock(content="APPROVE")
    ])
    # Mock parse_json method for LLM
    mock_llm_instance.parse_json = Mock(side_effect=[
        # ChangeSetGenerator's parse_json
        {
            "changes": [
                {
                    "operation": "REPLACE_BLOCK",
                    "anchor_id": "anc123",
                    "new_content": "This is the revised, concise introduction.",
                    "comment": "Rephrased for conciseness."
                }
            ]
        }
    ])

    # Patch the llm_with_cost_manager_from_llm_config method in Context
    mocker_patch = patch('metagpt.context.Context.llm_with_cost_manager_from_llm_config', return_value=mock_llm_instance)
    mocker_patch.start() # Start the patch

    # Create a mock RoleContext and add the initial message to its memory
    mock_rc_memory = Mock()
    draft_content = "[anchor-id::anc123]This is the original content that needs to be made more concise."
    initial_draft = FullDraft(content=draft_content)
    
    # Configure get_by_class to return specific messages in sequence
    mock_rc_memory.get_by_class.side_effect = [
        [Message(content="", instruct_content=initial_draft)], # For ChiefPM to get FullDraft
        [Message(content="", instruct_content=ReviewNotes(feedback="dummy"))], # For ChangeSetGenerator to get ReviewNotes
        [Message(content="", instruct_content=initial_draft)], # For ChangeSetGenerator to get FullDraft
        [Message(content="", instruct_content=initial_draft)], # For DocModifier to get FullDraft
        [Message(content="", instruct_content=QAReport(issues_found=[]))], # For ChiefPM to get QAReport (optional)
        [Message(content="", instruct_content=initial_draft)], # For ChiefPM to get FullDraft again
    ]

    # Create instances of the roles
    chief_pm = ChiefPM()
    changeset_generator = ChangeSetGenerator()
    doc_modifier = DocModifier()

    # Manually set the mocked RoleContext memory for each role
    chief_pm.rc.memory = mock_rc_memory
    changeset_generator.rc.memory = mock_rc_memory
    doc_modifier.rc.memory = mock_rc_memory

    print("--- Starting Revision Loop ---")

    # First Revision Cycle
    review_notes_msg = await chief_pm._act()
    print("ChiefPM Review Notes:", review_notes_msg.instruct_content.feedback)
    
    # Update memory for ChangeSetGenerator with the actual ReviewNotes message
    mock_rc_memory.get_by_class.side_effect = [
        [review_notes_msg], # For ChangeSetGenerator to get ReviewNotes
        [Message(content="", instruct_content=initial_draft)], # For ChangeSetGenerator to get FullDraft
        [Message(content="", instruct_content=initial_draft)], # For DocModifier to get FullDraft
        [Message(content="", instruct_content=QAReport(issues_found=[]))], # For ChiefPM to get QAReport (optional)
        [Message(content="", instruct_content=initial_draft)], # For ChiefPM to get FullDraft again
    ]

    changeset_msg = await changeset_generator._act()
    print("ChangeSet Generated:", changeset_msg.instruct_content.changes)
    
    # Simulate DocModifier applying changes
    # We need to get the latest FullDraft from memory for DocModifier
    current_draft_for_modifier = mock_rc_memory.get_by_class(FullDraft)[0].instruct_content.content
    modified_content = doc_modifier._apply_changes(current_draft_for_modifier, changeset_msg.instruct_content.changes)
    new_draft_after_mod = FullDraft(content=modified_content)
    print("Draft after modification:", new_draft_after_mod.content)
    
    # Simulate the new draft being added to memory for the next ChiefPM review
    mock_rc_memory.get_by_class.side_effect = [
        [Message(content="", instruct_content=new_draft_after_mod)], # For ChiefPM to get FullDraft
        [Message(content="", instruct_content=QAReport(issues_found=[]))], # For ChiefPM to get QAReport (optional)
    ]

    # Second Revision Cycle (should lead to approval)
    approval_msg = await chief_pm._act()
    print("ChiefPM Approval Status:", approval_msg.content)

    print("--- Revision Loop Finished ---")

    mocker_patch.stop() # Stop the patch

if __name__ == "__main__":
    asyncio.run(main())

    # Second Revision Cycle (should lead to approval)
    approval_msg = await chief_pm._act()
    print("ChiefPM Approval Status:", approval_msg.content)

    print("--- Revision Loop Finished ---")

    mocker_patch.stop() # Stop the patch

if __name__ == "__main__":
    asyncio.run(main())
