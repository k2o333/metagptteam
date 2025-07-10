from metagpt.actions import Action
from metagpt_doc_writer.schemas.doc_structures import InitialTask, RefinedTask
from metagpt.logs import logger

class RefineTask(Action):
    async def run(self, initial_task: InitialTask) -> RefinedTask:
        logger.warning("Running a legacy Action: RefineTask.")
        return RefinedTask(
            chapter_title=f"Refined: {initial_task.chapter_title}",
            context="This is a refined context.",
            goals=["Refined goal 1"],
            acceptance_criteria=["Refined criterion 1"]
        )