
from metagpt.actions import Action
from metagpt_doc_writer.schemas.doc_structures import InitialTask

class GenerateInitialTask(Action):
    async def run(self, module_outline: str) -> InitialTask:
        # In a real implementation, this would use an LLM to generate the initial task.
        # For now, we'll just create a dummy task.
        return InitialTask(chapter_title=f"Initial task for {module_outline}")
