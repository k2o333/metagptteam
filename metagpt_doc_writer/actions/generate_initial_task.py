# 路径: /root/metagpt/mgfr/metagpt_doc_writer/actions/generate_initial_task.py

from metagpt.actions import Action
from metagpt_doc_writer.schemas.doc_structures import InitialTask
from metagpt.logs import logger

class GenerateInitialTask(Action):
    async def run(self, module_title: str) -> InitialTask:
        logger.warning("Running a legacy Action: GenerateInitialTask.")
        return InitialTask(chapter_title=f"Initial task for {module_title}")