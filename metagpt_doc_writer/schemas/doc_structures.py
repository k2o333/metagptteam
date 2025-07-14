# /root/metagpt/mgfr/metagpt_doc_writer/schemas/doc_structures.py

import uuid
from pydantic import BaseModel, Field
from typing import List, Dict, Any

# ==============================================================================
#  核心数据结构 (Core Data Structures for the Final Architecture)
# ==============================================================================

class UserRequirement(BaseModel):
    """
    一个简单的、可序列化的Pydantic模型，用于表示初始用户需求。
    A simple, serializable Pydantic model for the initial user requirement.
    """
    content: str = Field(..., description="The user's initial idea or instruction.")

class Task(BaseModel):
    """
    定义了一个独立的、可执行的任务单元。
    Defines a single, executable task unit.
    """
    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:6]}")
    instruction: str = Field(..., description="对任务的具体、详细描述。A specific, detailed description of the task.")
    action_type: str = Field(..., description="执行此任务的通用动作类型，如'RESEARCH', 'WRITE', 'REVIEW'。The generic action type to perform this task.")
    context: Dict[str, Any] = Field(default_factory=dict, description="执行任务所需的上下文数据。Contextual data required to execute the task.")
    dependent_task_ids: List[str] = Field(default_factory=list, description="此任务依赖的其他任务ID。A list of other task IDs this task depends on.")
    use_tools: List[str] = Field(default_factory=list, description="执行此任务所需的工具列表，如['web_search']。List of tool names required for this task, e.g., ['web_search'].")
    result: str = Field("", description="此任务的执行结果。The execution result of this task.")

class Plan(BaseModel):
    """
    定义了整个项目的执行计划，由一系列有序的任务组成。
    Defines the execution plan for the entire project, consisting of a series of ordered tasks.
    """
    goal: str = Field(..., description="项目的最终目标。The ultimate goal of the project.")
    tasks: List[Task] = Field(default_factory=list, description="所有任务的列表。The list of all tasks.")
    task_map: Dict[str, Task] = Field(default_factory=dict, description="任务ID到任务对象的映射，便于快速查找。A map from task_id to the Task object for quick lookups.")

    def get_ready_tasks(self, completed_task_ids: List[str]) -> List[Task]:
        """
        根据已完成的任务ID列表，获取所有依赖已满足且尚未开始的新任务。
        Gets all new tasks whose dependencies are met, based on a list of completed task IDs.
        """
        ready_tasks = []
        completed_set = set(completed_task_ids)
        for task in self.tasks:
            if task.task_id not in completed_set and set(task.dependent_task_ids).issubset(completed_set):
                ready_tasks.append(task)
        return ready_tasks

class FinalDelivery(BaseModel):
    """
    一个信号Schema，表示最终产物已生成，并包含其路径。
    A signal schema indicating that the final product has been generated, including its path.
    """
    document_path: str = Field(..., description="Path to the final delivered document.")

# ------------------------------------------------------------------------------
#  注意：所有其他旧的、不再使用的Schema（如ProjectPlan, ModuleOutline,
#  InitialTask, RefinedTask, ApprovedTask, DraftSection, FullDraft, ReviewNotes,
#  Change, ValidatedChangeSet, Approval, ProjectArchived, QAFeedback, QAReport）
#  已从此文件中被完全移除，以确保代码库的整洁和避免导入错误。
# ------------------------------------------------------------------------------