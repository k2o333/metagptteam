
from metagpt.actions import Action
from metagpt_doc_writer.schemas.doc_structures import InitialTask

class GenerateInitialTask(Action):
    async def run(self, module_title: str) -> InitialTask:
        prompt = f"""
        You are a task dispatcher. Your goal is to generate an initial task description 
        from a given module title. The task should be concise and directly related to the module.

        Module Title: {module_title}

        Please provide the initial task description.
        """
        rsp = await self._aask(prompt)
        return InitialTask(chapter_title=rsp.content)
