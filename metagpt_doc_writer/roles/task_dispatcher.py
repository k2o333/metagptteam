# /root/metagpt/mgfr/metagpt_doc_writer/roles/task_dispatcher.py (最终简化版)

from .base_role import DocWriterBaseRole
from metagpt.actions import Action
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt_doc_writer.schemas.doc_structures import ModuleOutline, InitialTask
import asyncio

class GenerateInitialTask(Action):
    name: str = "GenerateInitialTask"
    async def run(self, chapter_title: str, *args, **kwargs) -> InitialTask:
        logger.info(f"Action: Generating initial task for '{chapter_title}'")
        return InitialTask(chapter_title=chapter_title)

class TaskDispatcher(DocWriterBaseRole):
    name: str = "TaskDispatcher"
    profile: str = "Task Dispatcher"
    goal: str = "Generate initial tasks from a module outline."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([GenerateInitialTask()])
        # 【核心修改】它现在只监听单个 ModuleOutline
        self._watch({ModuleOutline})
        self._set_react_mode(react_mode="by_order", max_react_loop=1)

    async def _act(self) -> Message:
        if not self.rc.todo: return None
        action = self.rc.todo
        logger.info(f"{self._setting}: ready to {action.name}")
        
        trigger_msg = self.rc.history[-1]
        module_outline = trigger_msg.instruct_content

        if not isinstance(module_outline, ModuleOutline):
            return None

        # 一次性为该大纲的所有章节创建初始任务
        tasks = [action.run(chapter_title=chapter_title) for chapter_title in module_outline.chapters]
        initial_tasks = await asyncio.gather(*tasks)

        if not initial_tasks:
            return None
        
        logger.info(f"TaskDispatcher created {len(initial_tasks)} initial tasks. Sending to Scheduler.")

        # 【核心修改】将包含列表的消息发送给 Scheduler
        return Message(
            content=f"Dispatching {len(initial_tasks)} initial tasks for refinement.",
            instruct_content=initial_tasks,
            role=self.profile,
            cause_by=type(action).__name__,
            send_to="Scheduler"
        )