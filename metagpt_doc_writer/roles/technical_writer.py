# 路径: /root/metagpt/mgfr/metagpt_doc_writer/roles/technical_writer.py (最终回执版)
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt_doc_writer.schemas.doc_structures import Task

class TechnicalWriter(Role):
    def __init__(self, name: str = "Executor", **kwargs):
        super().__init__(name=name, **kwargs)
        self._watch({Task})

    async def _act(self) -> Message:
        # 获取最新的、发给自己的任务消息
        task_msg = next((msg for msg in reversed(self.rc.news) if isinstance(msg.instruct_content, Task) and self.name in msg.send_to), None)
        
        if not task_msg:
             return None # 本轮没有给我的新任务

        task: Task = task_msg.instruct_content
        logger.info(f"{self.name} received task '{task.task_id}': {task.instruction}")

        target_action = next((action for action in self.actions if action.name == task.action_type), None)
        
        if not target_action:
            error_msg = f"Action type '{task.action_type}' not found in {self.name}'s actions."
            logger.error(error_msg)
            return Message(content=error_msg, send_to="Scheduler", instruct_content=task, role=self.name)

        context = task.context.get('dependency_results', '')
        result = await target_action.run(instruction=task.instruction, context=context)
        
        # [关键] 将包含结果和原Task对象的消息发送回Scheduler
        logger.info(f"Task '{task.task_id}' completed by {self.name}.")
        return Message(content=str(result), instruct_content=task, send_to="Scheduler", role=self.name)