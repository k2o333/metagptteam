# 路径: /root/metagpt/mgfr/metagpt_doc_writer/schemas/doc_structures.py (真正完整版)

import uuid
from pydantic import BaseModel, Field
from typing import List, Dict, Any

# --- 新增或修改的规划器模式数据结构 ---
class Task(BaseModel):
    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:6]}")
    instruction: str = Field(..., description="对任务的具体、详细描述")
    action_type: str = Field(..., description="执行此任务的通用动作类型，如'RESEARCH', 'WRITE', 'REVIEW'")
    context: Dict[str, Any] = Field(default_factory=dict, description="执行任务所需的上下文数据")
    dependent_task_ids: List[str] = Field(default_factory=list, description="此任务依赖的其他任务ID")

class Plan(BaseModel):
    goal: str = Field(..., description="项目的最终目标")
    tasks: List[Task] = Field(default_factory=list, description="所有任务的列表")
    task_map: Dict[str, Task] = Field(default_factory=dict, description="任务ID到任务对象的映射，便于快速查找")

    def add_task(self, **kwargs):
        task = Task(**kwargs)
        self.tasks.append(task)
        self.task_map[task.task_id] = task
        return task

    def get_ready_tasks(self, completed_task_ids: set) -> List[Task]:
        """获取所有依赖已完成的任务"""
        ready_tasks = []
        for task in self.tasks:
            if task.task_id not in completed_task_ids and set(task.dependent_task_ids).issubset(completed_task_ids):
                ready_tasks.append(task)
        return ready_tasks

# --- 您项目中已有的其他schemas (全部保留) ---
class ProjectPlan(BaseModel):
    modules: List[str] = Field(..., description="List of top-level module titles")

class ModuleOutline(BaseModel):
    module_title: str = Field(..., description="Title of the module")
    chapters: List[str] = Field(..., description="List of chapter titles in the module")

class InitialTask(BaseModel):
    chapter_title: str = Field(..., description="Title of the chapter to be written")

class RefinedTask(BaseModel):
    chapter_title: str = Field(..., description="Refined title of the chapter")
    context: str = Field(..., description="Context and background for the chapter")
    goals: List[str] = Field(..., description="Specific goals for the chapter content")
    acceptance_criteria: List[str] = Field(..., description="Criteria to accept the chapter")

class ApprovedTask(BaseModel):
    chapter_title: str = Field(..., description="Approved title of the chapter")
    refined_task: RefinedTask = Field(..., description="The refined task details")

class DraftSection(BaseModel):
    chapter_id: str = Field(..., description="Unique identifier for the chapter")
    content: str = Field(..., description="Draft content of the section/chapter")

class FullDraft(BaseModel):
    content: str = Field(..., description="Full content with embedded anchor IDs")
    version: int = 1

class ReviewNotes(BaseModel):
    feedback: str = Field(..., description="Natural language feedback on the draft")

class Change(BaseModel):
    operation: str = Field(..., description="e.g., REPLACE_BLOCK, INSERT_AFTER")
    anchor_id: str = Field(..., description="The unique ID of the anchor to operate on")
    anchor_id_end: str = ""
    new_content: str = ""
    comment: str

class ValidatedChangeSet(BaseModel):
    changes: List[Change]

class QAReport(BaseModel):
    issues_found: List[str] = Field(..., description="List of issues found during QA")

class FinalDelivery(BaseModel):
    document_path: str = Field(..., description="Path to the final delivered document")

class ProjectArchived(BaseModel):
    archive_path: str = Field(..., description="Path to the archived project files")