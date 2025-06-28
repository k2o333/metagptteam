
from pydantic import BaseModel, Field
from typing import List, Dict, Any

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
