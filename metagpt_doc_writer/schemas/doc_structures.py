# /root/metagpt/mgfr/metagpt_doc_writer/schemas/doc_structures.py

import uuid
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

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
    instruction: str = Field(..., description="对任务的具体、详细描述。")
    action_type: str = Field(..., description="执行此任务的通用动作类型，如'RESEARCH', 'WRITE', 'REVIEW'。")
    
    # 【核心字段】定义此任务操作的文档片段ID。可选，因为并非所有任务都产出可版本化的内容。
    target_snippet_id: Optional[str] = Field(None, description="The unique ID of the document snippet this task targets, if any.")
    
    context: Dict[str, Any] = Field(default_factory=dict, description="执行任务所需的上下文数据。")
    dependent_task_ids: List[str] = Field(default_factory=list, description="此任务依赖的其他任务ID。")
    use_tools: List[str] = Field(default_factory=list, description="执行此任务所需的工具列表。")
    result: str = Field("", description="此任务的执行结果。")

class Plan(BaseModel):
    """
    定义了整个项目的执行计划，由一系列有序的任务组成。
    """
    goal: str = Field(..., description="项目的最终目标。")
    tasks: List[Task] = Field(default_factory=list, description="所有任务的列表。")
    task_map: Dict[str, Task] = Field(default_factory=dict, description="任务ID到任务对象的映射，便于快速查找。")

    def get_ready_tasks(self, completed_task_ids: List[str]) -> List[Task]:
        """
        根据已完成的任务ID列表，获取所有依赖已满足且尚未开始的新任务。
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
    """
    document_path: str = Field(..., description="Path to the final delivered document.")

# ------------------------------------------------------------------------------
#  注意：所有其他旧的、不再使用的Schema都已从此文件中被完全移除。
# ------------------------------------------------------------------------------