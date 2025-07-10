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
    mocker.patch.object(BaseLLM, 'aask', side_effect=[
        mock_initial_draft_message,
        mock_reflection_message_low_score
    ])
    action = WriteSection()
    draft_section = await action.run(approved_task)
    assert draft_section.content == mock_reflection_response_low_score["Revise"]

    # Test case 2: High score, should return original draft
    mocker.patch.object(BaseLLM, 'aask', side_effect=[
        mock_initial_draft_message,
        mock_reflection_message_high_score
    ])
    action = WriteSection()
    draft_section = await action.run(approved_task)
    assert draft_section.content == mock_initial_draft_content