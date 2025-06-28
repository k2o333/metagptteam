
import pytest
from unittest.mock import patch
from metagpt_doc_writer.actions.refine_task import RefineTask
from metagpt_doc_writer.schemas.doc_structures import InitialTask

@pytest.mark.asyncio
async def test_refine_task_action():
    # No mocking needed for the dummy implementation
    action = RefineTask()
    initial_task = InitialTask(chapter_title="Test Title")
    refined_task = await action.run(initial_task)
    assert refined_task.goals is not None
    assert refined_task.chapter_title == "Refined: Test Title"
