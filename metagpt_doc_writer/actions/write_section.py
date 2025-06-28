
from metagpt.actions import Action
from metagpt_doc_writer.schemas.doc_structures import ApprovedTask, DraftSection

class WriteSection(Action):
    async def run(self, task: ApprovedTask) -> DraftSection:
        # In a real implementation, this would use an LLM with a self-reflection mechanism.
        # For now, we'll just create a dummy draft section.
        return DraftSection(
            chapter_id=task.chapter_title, # Using title as ID for simplicity
            content=f"This is the draft content for {task.chapter_title}."
        )
