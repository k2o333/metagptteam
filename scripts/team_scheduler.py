# 路径: /root/metagpt/mgfr/scripts/team_scheduler.py (这是一个新文件)

import asyncio
from typing import Dict, Any
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt_doc_writer.schemas.doc_structures import Plan, Task

class Scheduler:
    def __init__(self, plan: Plan, roles: Dict[str, Role]):
        """
        一个专为流水线任务设计的调度器。
        :param plan: 从Planner获取的完整计划。
        :param roles: 一个字典，key是action_type (e.g., "RESEARCH"), value是可以执行该action的Role实例。
        """
        self.plan = plan
        self.roles_map = roles
        self.completed_tasks = set()
        self.task_results: Dict[str, Any] = {}
        self.dispatched_tasks = set()

    async def run(self):
        """
        运行整个计划，直到所有任务完成或无法继续。
        """
        while len(self.completed_tasks) < len(self.plan.tasks):
            # 获取所有依赖已完成的任务
            ready_tasks = [
                task for task in self.plan.tasks
                if task.task_id not in self.completed_tasks and
                   task.task_id not in self.dispatched_tasks and
                   set(task.dependent_task_ids).issubset(self.completed_tasks)
            ]

            if not ready_tasks:
                if len(self.completed_tasks) < len(self.plan.tasks):
                    logger.warning("没有可执行的任务，但计划尚未完成。可能存在任务依赖循环或错误。调度器停止。")
                break # 结束循环

            # 将所有就绪的任务标记为已分派
            for task in ready_tasks:
                self.dispatched_tasks.add(task.task_id)

            # 并行执行所有就绪的任务
            task_coroutines = [self.execute_task(task) for task in ready_tasks]
            results = await asyncio.gather(*task_coroutines, return_exceptions=True)

            # 处理执行结果
            for task, result in zip(ready_tasks, results):
                if isinstance(result, Exception):
                    logger.error(f"❌ 任务 '{task.task_id}: {task.instruction}' 执行失败，异常: {result}", exc_info=result)
                    logger.error("由于任务执行失败，调度器已停止。")
                    return # 遇到错误，终止整个流程
                else:
                    self.completed_tasks.add(task.task_id)
                    self.task_results[task.task_id] = result
                    logger.info(f"✅ 任务 '{task.task_id}: {task.instruction}' 已完成。")
        
        logger.info("🎉 全部任务已成功完成！")

    async def execute_task(self, task: Task) -> Any:
        """
        执行单个任务。
        """
        logger.info(f"🚀 开始执行任务 '{task.task_id}': {task.instruction}")
        
        action_type = task.action_type
        
        # 找到能执行此Action的Role
        role = self.roles_map.get(action_type)
        if not role:
            raise ValueError(f"在roles_map中找不到可以执行action_type '{action_type}'的角色")
        
        # 找到具体的Action
        target_action = next((action for action in role.actions if action.name == action_type), None)
        if not target_action:
            raise ValueError(f"角色'{role.name}'中找不到名为'{action_type}'的Action")

        # 准备上下文信息
        context_parts = []
        for dep_id in task.dependent_task_ids:
            if dep_id in self.task_results:
                context_parts.append(
                    f"### Context from dependent task '{dep_id}':\n{self.task_results[dep_id]}"
                )
        
        context_str = "\n\n---\n\n".join(context_parts)
        
        # 执行Action
        return await target_action.run(instruction=task.instruction, context=context_str)