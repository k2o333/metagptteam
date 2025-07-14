# /root/metagpt/mgfr/metagpt_doc_writer/roles/executor.py (已修正)

from .base_role import DocWriterBaseRole
from metagpt.schema import Message
from metagpt.logs import logger  # <--- 正确的拼写
from metagpt_doc_writer.schemas.doc_structures import Task
from metagpt_doc_writer.actions.research import Research
from metagpt_doc_writer.actions.write import Write
from metagpt_doc_writer.actions.review import Review

class Executor(DocWriterBaseRole):
    name: str = "Executor"
    profile: str = "Task Executor"
    goal: str = "Execute tasks of various types (RESEARCH, WRITE, REVIEW) as instructed."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Actions仍然需要被初始化
        self.set_actions([Research(), Write(), Review()])

    # run方法是主要入口
    async def run(self, task_msg: Message) -> Message:
        task: Task = task_msg.instruct_content
        if not isinstance(task, Task):
            return Message(content="Error: Invalid task message received.")

        logger.info(f"Executor received task '{task.task_id}' with action type '{task.action_type}'.")
        
        action_to_run = next((act for act in self.actions if act.name == task.action_type), None)
        
        if not action_to_run:
            error_msg = f"No action found for type '{task.action_type}'"
            logger.error(error_msg)
            return Message(content=error_msg, instruct_content=task, role=self.profile)

        # 注入 LLM 实例给 Action
        action_to_run.set_llm(self.llm)

        result = await action_to_run.run(
            instruction=task.instruction, 
            context=task.context.get('dependency_results', '')
        )

        return Message(content=result, instruct_content=task, role=self.profile)