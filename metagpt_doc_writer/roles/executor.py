# /root/metagpt/mgfr/metagpt_doc_writer/roles/executor.py

from .base_role import DocWriterBaseRole
from metagpt.logs import logger
from metagpt_doc_writer.schemas.doc_structures import Task
from metagpt_doc_writer.actions.research import Research
from metagpt_doc_writer.actions.write import Write
from metagpt_doc_writer.actions.review import Review
from typing import Dict

class Executor(DocWriterBaseRole):
    name: str = "Executor"
    profile: str = "Task Executor"
    goal: str = "Execute tasks by dispatching resources to the appropriate actions."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([Research, Write, Review])

    async def run(self, task: Task, completed_tasks: Dict[str, Task]) -> Task:
        """
        接收一个任务，准备资源，执行它，并返回更新了结果的任务对象。
        """
        logger.info(f"Executor received task '{task.task_id}' with type '{task.action_type}'.")
        
        action_to_run = next((act for act in self.actions if act.name == task.action_type), None)
        
        if not action_to_run:
            task.result = f"Error: No action found for type '{task.action_type}'"
            logger.error(task.result)
            return task

        if not action_to_run.llm:
            action_to_run.set_llm(self.llm)

        context_str = "\n\n---\n\n".join([
            f"### Context from dependent task '{dep_id}':\nInstruction: '{completed_tasks[dep_id].instruction}'\n\nResult:\n{completed_tasks[dep_id].result}"
            for dep_id in task.dependent_task_ids if dep_id in completed_tasks
        ])
        
        # 准备一个统一的、包含所有潜在资源的参数字典
        action_kwargs = {
            "instruction": task.instruction,
            "context": context_str,
            "enable_web_search": "web_search" in task.use_tools,
            "mcp_manager": self.mcp_manager,
            "mcp_permissions": {
                tool_name: self.can_use_mcp_tool(tool_name)
                for tool_name in task.use_tools if tool_name != "web_search"
            }
        }
        
        if action_kwargs["enable_web_search"]:
            logger.info(f"Task '{task.task_id}' requires 'web_search'. Enabling SearchEngine for Action.")
        if action_kwargs["mcp_permissions"]:
            logger.info(f"Task '{task.task_id}' requires MCP tools. Passing permissions: {action_kwargs['mcp_permissions']}")

        # 使用 **kwargs 解包，将统一的参数集传递给任何Action
        action_result = await action_to_run.run(**action_kwargs)
        task.result = action_result
        
        return task