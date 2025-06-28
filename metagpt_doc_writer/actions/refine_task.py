
from metagpt.actions import Action
from metagpt_doc_writer.schemas.doc_structures import InitialTask, RefinedTask

class RefineTask(Action):
    async def run(self, initial_task: InitialTask) -> RefinedTask:
        # In a real implementation, this would use an LLM with a CoT prompt to refine the task.
        # For now, we'll just create a dummy refined task.
        return RefinedTask(
            chapter_title=f"Refined: {initial_task.chapter_title}",
            context="This is the context for the refined task.",
            goals=["Goal 1", "Goal 2"],
            acceptance_criteria=["Criterion 1", "Criterion 2"]
        )
