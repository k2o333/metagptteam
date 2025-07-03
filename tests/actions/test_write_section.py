import pytest
from metagpt_doc_writer.actions.write_section import WriteSection
from metagpt_doc_writer.schemas.doc_structures import ApprovedTask, RefinedTask
from metagpt.provider.base_llm import BaseLLM
from metagpt.schema import Message
import json

@pytest.mark.asyncio
async def test_write_section_with_reflection(mocker):
    # Mock the LLM for initial draft generation
    mock_initial_draft_content = "This is an initial draft with some flaws."
    mock_initial_draft_message = Message(content=mock_initial_draft_content)

    # Mock the LLM for self-reflection (first call - low score, needs revision)
    mock_reflection_response_low_score = {
        "Evaluate": {"Completeness": 2, "Clarity": 2, "Accuracy": 2}, # Total 6, < 13
        "Suggest": "Improve clarity and add more details.",
        "Revise": "This is the revised and improved draft."
    }
    mock_reflection_message_low_score = Message(content=json.dumps(mock_reflection_response_low_score))

    # Mock the LLM for self-reflection (second call - high score, no revision needed)
    mock_reflection_response_high_score = {
        "Evaluate": {"Completeness": 5, "Clarity": 5, "Accuracy": 5}, # Total 15, >= 13
        "Suggest": "None",
        "Revise": ""
    }
    mock_reflection_message_high_score = Message(content=json.dumps(mock_reflection_response_high_score))

    # Create a mock LLM instance
    mock_llm = mocker.Mock(spec=BaseLLM)
    mock_llm.aask.side_effect = [
        mock_initial_draft_message,  # First call for initial draft
        mock_reflection_message_low_score, # Second call for reflection (low score)
        mock_initial_draft_message,  # Third call for initial draft (for second test case)
        mock_reflection_message_high_score # Fourth call for reflection (high score)
    ]

    # Create an ApprovedTask instance
    approved_task = ApprovedTask(
        chapter_title="Test Chapter",
        refined_task=RefinedTask(
            chapter_title="Test Chapter",
            context="Context for testing",
            goals=["Goal 1", "Goal 2"],
            acceptance_criteria=["Criteria 1", "Criteria 2"]
        )
    )

    # Test case 1: Low score, should return revised draft
    action = WriteSection(llm=mock_llm)
    draft_section = await action.run(approved_task)

    assert draft_section.content == mock_reflection_response_low_score["Revise"]
    assert mock_llm.aask.call_count == 2 # Initial draft + reflection
    mock_llm.aask.reset_mock()

    # Test case 2: High score, should return original draft
    action = WriteSection(llm=mock_llm)
    draft_section = await action.run(approved_task)

    assert draft_section.content == mock_initial_draft_content
    assert mock_llm.aask.call_count == 2 # Initial draft + reflection