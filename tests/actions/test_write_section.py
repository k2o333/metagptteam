
import pytest
from metagpt_doc_writer.actions.write_section import WriteSection
from metagpt_doc_writer.schemas.doc_structures import ApprovedTask, RefinedTask

@pytest.mark.asyncio
async def test_write_section_action():
    # No mocking needed for the dummy implementation
    action = WriteSection()
    refined_task = RefinedTask(
        chapter_title="Test Chapter",
        context="Test context",
        goals=["Goal 1"],
        acceptance_criteria=["Criterion 1"]
    )
    approved_task = ApprovedTask(chapter_title="Test Chapter", refined_task=refined_task)
    draft_section = await action.run(approved_task)
    assert draft_section.content is not None
    assert "Test Chapter" in draft_section.content
