# /root/metagpt/mgfr/metagpt_doc_writer/roles/task_refiner.py (已修改)

from .base_role import DocWriterBaseRole
from metagpt.actions import Action
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt.utils.common import OutputParser
from metagpt_doc_writer.schemas.doc_structures import InitialTask, RefinedTask
from .task_dispatcher import GenerateInitialTask

class RefineTask(Action):
    name: str = "RefineTask"
    async def run(self, initial_task: InitialTask, use_llm: bool = False) -> RefinedTask:
        if not use_llm:
            logger.warning(f"RefineTask is using MOCK data for '{initial_task.chapter_title}'.")
            return RefinedTask(
                chapter_title=f"Refined: {initial_task.chapter_title}",
                context="This is a mocked refined context.",
                goals=["Mocked goal 1"],
                acceptance_criteria=["Mocked criterion 1"]
            )

        logger.info(f"Action: Refining task for '{initial_task.chapter_title}' with LLM...")
        prompt = f"""
        You are a senior technical writer. Refine the following simple task into a detailed, actionable task description.
        Initial Task Title: "{initial_task.chapter_title}"
        Provide a detailed context, 2-3 specific goals, and 2-3 clear acceptance criteria.
        Respond ONLY with a valid JSON object: {{"chapter_title": "...", "context": "...", "goals": ["..."], "acceptance_criteria": ["..."]}}
        """
        response_str = await self._aask(prompt)
        try:
            data_dict = OutputParser.parse_code(text=response_str, lang="json")
            if isinstance(data_dict, str):
                import json
                data_dict = json.loads(data_dict)
            return RefinedTask(**data_dict)
        except Exception as e:
            logger.error(f"Failed to parse LLM for RefineTask: {e}\nRaw response:\n{response_str}")
            return RefinedTask(chapter_title=f"Refined: {initial_task.chapter_title} (Parsing Error)", context="", goals=[], acceptance_criteria=[])

class TaskRefiner(DocWriterBaseRole):
    name: str = "TaskRefiner"
    profile: str = "Task Refiner"
    goal: str = "Refine initial tasks to make them more detailed and actionable"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([RefineTask()])
        self._watch({f"{GenerateInitialTask.__module__}.{GenerateInitialTask.__name__}"})
        self._set_react_mode(react_mode="by_order", max_react_loop=1)

    async def _act(self) -> Message:
        if not self.rc.todo: return None
        action = self.rc.todo
        logger.info(f"{self._setting}: ready to {action.name}")
        
        initial_task_msg = self.rc.history[-1]
        initial_task = initial_task_msg.instruct_content

        if not isinstance(initial_task, InitialTask):
            logger.warning(f"Expected InitialTask, but got {type(initial_task)}. Skipping.")
            return None

        use_llm = self.llm_activation.get(action.name, False)
        refined_task = await action.run(initial_task, use_llm=use_llm)
        
        # --- 添加日志点 A ---
        logger.success(f"TaskRefiner: Successfully created RefinedTask for '{refined_task.chapter_title}'. Preparing to publish.")
        
        return Message(content=refined_task.model_dump_json(), instruct_content=refined_task, cause_by=type(action))