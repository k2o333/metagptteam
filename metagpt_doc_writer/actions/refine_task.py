
from metagpt.actions import Action
from metagpt.utils.common import OutputParser
from metagpt_doc_writer.schemas.doc_structures import InitialTask, RefinedTask

class RefineTask(Action):
    async def run(self, initial_task: InitialTask) -> RefinedTask:
        prompt = f"""
        You are a task refiner. Your goal is to take an initial task description and refine it 
        into a more detailed and actionable task, including context, specific goals, and acceptance criteria.
        Use Chain-of-Thought (CoT) reasoning to arrive at the refined task.

        Initial Task:
        Title: {initial_task.chapter_title}

        Think step by step:
        1. What additional context is needed for this task?
        2. What are the specific, measurable goals for this task?
        3. What are the clear acceptance criteria to determine if the task is complete and successful?

        Provide the refined task in the following JSON format:
        {{
            "chapter_title": "<refined_title>",
            "context": "<detailed_context>",
            "goals": ["<goal1>", "<goal2>"],
            "acceptance_criteria": ["<criterion1>", "<criterion2>"]
        }}
        """
        rsp = await self._aask(prompt)
        # Assuming rsp.content is a valid JSON string
        refined_task_data = OutputParser.extract_struct(rsp.content, dict)
        return RefinedTask(**refined_task_data)
