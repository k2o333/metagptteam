# /root/metagpt/mgfr/metagpt_doc_writer/roles/task_dispatcher.py (已修改)

from .base_role import DocWriterBaseRole
from metagpt.actions import Action
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt_doc_writer.schemas.doc_structures import ModuleOutline, InitialTask
from .group_pm import CreateModuleOutline

class GenerateInitialTask(Action):
    name: str = "GenerateInitialTask"
    async def run(self, chapter_title: str, *args, **kwargs) -> InitialTask:
        logger.info(f"Action: Generating initial task for '{chapter_title}'")
        return InitialTask(chapter_title=chapter_title)

class TaskDispatcher(DocWriterBaseRole):
    name: str = "TaskDispatcher"
    profile: str = "Task Dispatcher"
    goal: str = "Generate initial tasks from module outlines"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([GenerateInitialTask])
        self._watch({f"{CreateModuleOutline.__module__}.{CreateModuleOutline.__name__}"})

    async def _act(self) -> Message:
        logger.info(f"{self.name}: Ready to dispatch tasks.")
        
        # FIX: 不再只看 history[-1]，而是处理所有新消息
        # 遍历 self.rc.news 里的所有 ModuleOutline 消息
        module_outline_msgs = [m for m in self.rc.news if isinstance(m.instruct_content, ModuleOutline)]
        if not module_outline_msgs:
            logger.warning(f"{self.name}: No new ModuleOutline messages to process.")
            return None

        action = self.rc.todo
        if not action:
            logger.warning(f"{self.name}: No action to perform (todo is None).")
            return None
        
        # 对每一个大纲都进行处理
        for module_outline_msg in module_outline_msgs:
            module_outline = module_outline_msg.instruct_content
            logger.info(f"Dispatching tasks for module: '{module_outline.module_title}'")
            
            for chapter_title in module_outline.chapters:
                initial_task: InitialTask = await action.run(chapter_title=chapter_title)
                
                msg_to_publish = Message(
                    content=f"Initial task for chapter '{initial_task.chapter_title}' created.",
                    instruct_content=initial_task,
                    role=self.profile,
                    cause_by=type(action)
                )
                self.rc.env.publish_message(msg_to_publish)
        
        # 所有工作都通过 publish_message 完成，返回 None
        return None