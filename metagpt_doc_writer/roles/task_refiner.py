# /root/metagpt/mgfr/metagpt_doc_writer/roles/task_refiner.py (已修改)

import asyncio
from .base_role import DocWriterBaseRole
from metagpt.actions import Action
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt.utils.common import OutputParser
from metagpt_doc_writer.schemas.doc_structures import InitialTask, RefinedTask

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
        # FIX: 监听 InitialTask 数据类型
        self._watch({InitialTask})
        self._set_react_mode(react_mode="by_order", max_react_loop=1)

    async def _act(self) -> Message:
        if not self.rc.todo: return None
        action = self.rc.todo
        logger.info(f"{self._setting}: ready to {action.name}")
        
        trigger_msg = self.rc.history[-1]
        content = trigger_msg.instruct_content
        initial_tasks = content if isinstance(content, list) else [content]

        use_llm = self.llm_activation.get(action.name, False)
        
        # --- 【核心修正】: 并发处理所有 InitialTask ---
        tasks_to_run = [action.run(task, use_llm=use_llm) for task in initial_tasks if isinstance(task, InitialTask)]
        
        if not tasks_to_run:
            logger.warning("TaskRefiner: No valid InitialTask objects to process.")
            return None

        refined_tasks = await asyncio.gather(*tasks_to_run)
        
        if not refined_tasks:
            logger.warning("TaskRefiner: No tasks were refined.")
            return None

        logger.info(f"TaskRefiner has refined {len(refined_tasks)} tasks.")

        # 将所有精炼后的任务列表作为 instruct_content 返回
        # ChiefPM 会接收到这个列表，并逐一审批
        return Message(
            content=f"Refined {len(refined_tasks)} tasks.",
            instruct_content=refined_tasks,
            role=self.profile,
            cause_by=type(action).__name__
        )