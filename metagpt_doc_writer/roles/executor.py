# /root/metagpt/mgfr/metagpt_doc_writer/roles/executor.py

from .base_role import DocWriterBaseRole
from metagpt.logs import logger
from metagpt.actions.action import Action
from metagpt_doc_writer.schemas.doc_structures import Task
from typing import Dict, Any, Type

# 导入所有需要用到的Action类
from metagpt_doc_writer.actions.research import Research
from metagpt_doc_writer.actions.write import Write
from metagpt_doc_writer.actions.review import Review
from metagpt_doc_writer.actions.revise import Revise

class Executor(DocWriterBaseRole):
    name: str = "Executor"
    profile: str = "Task Executor"
    goal: str = "Execute a plan step-by-step, ensuring actions have the right context and resources."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 传递Action的类，让框架处理实例化和依赖注入
        self.set_actions([
            Research,
            Write,
            Review,
            Revise,
        ])
        logger.info(f"Executor initialized. Available action class names: {[act.__class__.__name__ for act in self.actions]}")
        
    async def run(
        self, 
        task: Task, 
        completed_tasks: Dict[str, Task],
        document_snippets: Dict[str, str]
    ) -> Task:
        """
        被外部调度器(run.py)调用的主要入口。
        """
        logger.info(f"Executor received task '{task.task_id}' with type '{task.action_type}'.")
        
        # 1. 使用Action的类名进行匹配
        action_to_run = next((act for act in self.actions if act.__class__.__name__ == task.action_type), None)
        
        # 【核心修正】: 为if语句提供正确的缩进代码块
        if not action_to_run:
            available_actions = [act.__class__.__name__ for act in self.actions]
            raise ValueError(f"Executor has no action for type '{task.action_type}'. Available actions: {available_actions}")

        # 2. 准备上下文
        context_str = "\n\n---\n\n".join([
            f"### Context from dependent task '{dep_id}':\n"
            f"Result:\n{completed_tasks[dep_id].result}"
            for dep_id in task.dependent_task_ids if dep_id in completed_tasks
        ])
        
        # 3. 准备传递给Action.run的参数
        action_kwargs: Dict[str, Any] = {
            "instruction": task.instruction,
            "context": context_str,
        }

        # 4. 为Revise任务准备artifact
        if task.action_type == "Revise":
            if task.target_snippet_id:
                action_kwargs["artifact"] = document_snippets.get(task.target_snippet_id, "")
                if not action_kwargs["artifact"]:
                    logger.warning(f"Revise task for snippet '{task.target_snippet_id}' has no prior artifact.")
            else:
                raise ValueError(f"Revise task '{task.task_id}' is missing a 'target_snippet_id'.")
        
        # 5. 执行Action
        action_result = await action_to_run.run(**action_kwargs)
        task.result = action_result
        
        return task