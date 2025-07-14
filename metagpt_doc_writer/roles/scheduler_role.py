# /root/metagpt/mgfr/metagpt_doc_writer/roles/scheduler_role.py (重构为状态机)

import asyncio
from .base_role import DocWriterBaseRole
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt_doc_writer.schemas.doc_structures import Plan, Task

class SchedulerRole(DocWriterBaseRole):
    name: str = "Scheduler"
    profile: str = "Task Scheduler"
    goal: str = "Execute a given plan by dispatching tasks to appropriate roles."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plan: Plan = None
        self.completed_tasks: set[str] = set()
        self.dispatched_tasks: set[str] = set()
        self.task_results: dict = {}
        
        # 监听Plan来启动，并监听Executor完成的Task来更新状态
        self._watch({Plan, Task}) 
        self.set_actions([])

    async def _observe(self) -> int:
        await super()._observe()
        
        for msg in reversed(self.rc.news):
            if not self.plan and isinstance(msg.instruct_content, Plan):
                self.plan = msg.instruct_content
                logger.info(f"Scheduler has received the plan with {len(self.plan.tasks)} tasks.")
                self.rc.news = []
                return 1 # 有新状态，需要行动

            # 我们约定Executor会把完成的Task对象作为instruct_content发回来
            if isinstance(msg.instruct_content, Task) and msg.role == "Executor":
                task = msg.instruct_content
                if task.task_id not in self.completed_tasks:
                    logger.success(f"Scheduler received completion for task '{task.task_id}'.")
                    self.completed_tasks.add(task.task_id)
                    self.task_results[task.task_id] = msg.content
                    self.rc.news = []
                    return 1 # 有新状态，需要行动
        return len(self.rc.news)

    async def _act(self) -> Message:
        if not self.plan:
            return None

        if len(self.completed_tasks) >= len(self.plan.tasks):
            logger.info("🎉 All tasks are completed. Scheduler is done.")
            return Message(content="ALL_TASKS_COMPLETED") # 发出最终信号

        ready_tasks = self.plan.get_ready_tasks(self.completed_tasks)
        tasks_to_dispatch = [t for t in ready_tasks if t.task_id not in self.dispatched_tasks]

        if not tasks_to_dispatch:
            logger.info("No new tasks are ready to be dispatched, waiting for dependencies.")
            return None

        # 分派所有准备好的任务
        for task in tasks_to_dispatch:
            logger.info(f"🚀 Dispatching task '{task.task_id}': {task.instruction}")
            
            # 准备上下文
            context_str = "\n---\n".join([
                f"### Result from dependent task '{dep_id}':\n{self.task_results.get(dep_id, '')}"
                for dep_id in task.dependent_task_ids
            ])
            # 将上下文放入Task对象，传递给执行者
            task.context['dependency_results'] = context_str

            # 创建任务消息，直接发送给Executor
            msg = Message(
                content=task.instruction,
                instruct_content=task,
                send_to="Executor" 
            )
            self.rc.env.publish(msg) # 使用publish而非publish_message，语义更清晰
            self.dispatched_tasks.add(task.task_id)

        return None # 分派任务后，等待执行者完成并返回消息