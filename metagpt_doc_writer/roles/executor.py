# /root/metagpt/mgfr/metagpt_doc_writer/roles/executor.py (最终修正版 V2)

from .base_role import DocWriterBaseRole
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt_doc_writer.schemas.doc_structures import Task
from metagpt_doc_writer.actions.research import Research
from metagpt_doc_writer.actions.write import Write
from metagpt_doc_writer.actions.review import Review
from typing import Dict

class Executor(DocWriterBaseRole):
    name: str = "Executor"
    profile: str = "Task Executor"
    goal: str = "Execute tasks of various types (RESEARCH, WRITE, REVIEW) as instructed."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 传递类，而不是实例。set_actions会处理实例化和注入context
        self.set_actions([Research, Write, Review])

    async def run(self, task: Task, completed_tasks: Dict[str, Task]) -> Task:
        """
        接收一个任务，执行它，并返回更新了结果的同一个任务对象。
        """
        logger.info(f"Executor received task '{task.task_id}' with action type '{task.action_type}'.")
        
        action_to_run = next((act for act in self.actions if act.name == task.action_type), None)
        
        if not action_to_run:
            task.result = f"Error: No action found for type '{task.action_type}'"
            logger.error(task.result)
            return task

        # 手动注入LLM，因为我们是外部调度
        action_to_run.set_llm(self.llm)

        context_str = "\n\n---\n\n".join([
            f"### Context from dependent task '{dep_id}':\nInstruction: '{completed_tasks[dep_id].instruction}'\n\nResult:\n{completed_tasks[dep_id].result}"
            for dep_id in task.dependent_task_ids if dep_id in completed_tasks
        ])
        
        # 【核心修正】: 在Role层面进行权限检查和依赖准备
        action_kwargs = {
            "instruction": task.instruction,
            "context": context_str
        }
        
        # 如果任务需要工具，由Role来检查权限并传递资源
        if "web_search" in task.use_tools:
            can_use = self.can_use_mcp_tool("web_search")
            action_kwargs["can_use_tool"] = can_use
            if can_use:
                # 只在有权限时才传递manager
                action_kwargs["mcp_manager"] = self.mcp_manager

        # Action的run方法现在接收一个明确的参数集
        action_result = await action_to_run.run(**action_kwargs)
        task.result = action_result
        
        return task