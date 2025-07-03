
import pytest
from unittest.mock import patch
from metagpt_doc_writer.actions.refine_task import RefineTask
from metagpt_doc_writer.schemas.doc_structures import InitialTask
from metagpt.schema import Message

@pytest.mark.asyncio
async def test_refine_task_action(mocker):
    mock_llm_response = '{"chapter_title": "Refined: Test Title", "context": "Refined context", "goals": ["Refined Goal 1"], "acceptance_criteria": ["Refined Criteria 1"]}'
    mocker.patch('metagpt.provider.base_llm.BaseLLM.aask', return_value=Message(content=mock_llm_response))

    action = RefineTask()
    initial_task = InitialTask(chapter_title="Test Title")
    refined_task = await action.run(initial_task)
    assert refined_task.goals is not None
    assert refined_task.chapter_title == "Refined: Test Title"
