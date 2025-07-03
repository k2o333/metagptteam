
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from metagpt.schema import Message
from metagpt.context import Context
from metagpt.roles.role import RoleContext
from metagpt_doc_writer.roles.technical_writer import TechnicalWriter
from metagpt_doc_writer.schemas.doc_structures import ApprovedTask, RefinedTask, DraftSection

async def main():
    # Mock the LLM creation to prevent actual LLM initialization errors
    mock_llm_instance = Mock()
    mock_llm_instance.system_prompt = ""
    # Mock _aask method for actions with AsyncMock
    mock_llm_instance.aask = AsyncMock(side_effect=[
        # Response for initial draft
        Mock(content="Initial draft content for Test Chapter."),
        # Response for reflection (revised draft)
        Mock(content='''
        {
            "evaluation": "Good",
            "suggestions": "None",
            "revised_draft": "Revised draft content for Test Chapter after self-reflection."
        }
        ''')
    ])
    # Mock parse_json method for LLM
    mock_llm_instance.parse_json = Mock(side_effect=[
        # Response for reflection's parse_json
        {
            "evaluation": "Good",
            "suggestions": "None",
            "revised_draft": "Revised draft content for Test Chapter after self-reflection."
        }
    ])
    # Patch the llm_with_cost_manager_from_llm_config method in Context
    mocker_patch = patch('metagpt.context.Context.llm_with_cost_manager_from_llm_config', return_value=mock_llm_instance)
    mocker_patch.start() # Start the patch

    # Create a mock RoleContext and add the initial message to its memory
    mock_rc_memory = Mock()
    refined_task = RefinedTask(
        chapter_title="Test Chapter",
        context="Test context",
        goals=["Goal 1"],
        acceptance_criteria=["Criterion 1"]
    )
    approved_task = ApprovedTask(chapter_title="Test Chapter", refined_task=refined_task)
    mock_rc_memory.get_by_class.return_value = [Message(content="", instruct_content=approved_task)]

    # Create an instance of the role
    writer = TechnicalWriter()

    # Manually set the mocked RoleContext memory for the role
    writer.rc.memory = mock_rc_memory

    # Run the writer
    draft_section_msg = await writer._act()
    print("Draft Section:", draft_section_msg.instruct_content)

    # Assertions
    assert isinstance(draft_section_msg.instruct_content, DraftSection)
    assert "Revised draft content" in draft_section_msg.instruct_content.content

    mocker_patch.stop() # Stop the patch

if __name__ == "__main__":
    asyncio.run(main())
