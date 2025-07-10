# 路径: /root/metagpt/mgfr/metagagpt_doc_writer/roles/scheduler_role.py (最终状态机版)

import asyncio
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt_doc_writer.schemas.doc_structures import Plan, Task

class SchedulerRole(Role):
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
        """
        重写 _observe 方法来处理进入的消息，并更新内部状态。
        """
        await super()._observe()
        
        # 逆序处理消息，确保最新的消息先被处理
        for msg in reversed(self.rc.news):
            # 1. 如果还没有计划，就寻找Plan消息
            if not self.plan and isinstance(msg.instruct_content, Plan):
                self.plan = msg.instruct_content
                logger.info(f"Scheduler has received the plan with {len(self.plan.tasks)} tasks.")
                # 清空news，因为Plan已经被处理了
                self.rc.news = []
                return 1 # 返回1表示有新状态，需要行动

            # 2. 更新已完成任务的状态
            # 我们约定Executor会把完成的Task对象作为instruct_content发回来
            if isinstance(msg.instruct_content, Task) and msg.role == "Executor":
                task = msg.instruct_content
                if task.task_id not in self.completed_tasks:
                    logger.info(f"Scheduler received completion for task '{task.task_id}'.")
                    self.completed_tasks.add(task.task_id)
                    self.task_results[task.task_id] = msg.content # 保存结果
                    # 清空news，因为这条完成消息已经被处理
                    self.rc.news = []
                    return 1 # 返回1表示有新状态，需要行动

        return len(self.rc.news)

    async def _act(self) -> Message:
        """
        根据当前状态（plan, completed_tasks）来决定是否分派新任务。
        """
        if not self.plan:
            logger.info("Scheduler is waiting for a plan.")
            return None # 没有计划，无事可做

        if len(self.completed_tasks) >= len(self.plan.tasks):
            logger.info("All tasks are completed. Scheduler is publishing the final signal.")
            # 所有任务完成，发布一个最终消息
            return Message(content="ALL_TASKS_COMPLETED")

        # 查找可以开始的新任务
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
            task.context['dependency_results'] = context_str

            # 创建任务消息，发送给Executor
            msg = Message(
                content=task.instruction,
                instruct_content=task,
                send_to="Executor" 
            )
            self.rc.env.publish(msg)
            self.dispatched_tasks.add(task.task_id)

        return None # 分派任务后，等待执行者完成并返回消息