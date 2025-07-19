# hierarchical/schemas.py
from __future__ import annotations
import uuid
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Section(BaseModel):
    """代表文档中的一个章节或子章节，是文档树的节点。"""
    section_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    display_id: str = Field("", description="用于展示的、带层级的ID，如 '1', '1.2'")
    title: str
    level: int
    content: str = ""
    status: str = Field("PENDING_OUTLINE", description="生命周期状态: PENDING_WRITE, COMPLETED, PENDING_SUBDIVIDE")
    parent_id: Optional[str] = None
    sub_sections: List[Section] = Field(default_factory=list)
    last_modified: datetime = Field(default_factory=datetime.now)

    def model_post_init(self, __context):
        if not self.display_id:
            self.display_id = self.title # 默认为标题

# Pydantic v2. `model_rebuild` replaces `update_forward_refs`.
Section.model_rebuild()

class Outline(BaseModel):
    """代表整个文档的、可演化的树状结构。"""
    goal: str
    root_sections: List[Section] = Field(default_factory=list)

    def find_section(self, section_id: str, search_in: Optional[List[Section]] = None) -> Optional[Section]:
        """递归地在整个大纲树中通过 section_id 查找章节。"""
        if search_in is None:
            search_in = self.root_sections

        for section in search_in:
            if section.section_id == section_id:
                return section
            found = self.find_section(section_id, section.sub_sections)
            if found:
                return found
        return None

    def model_dump_json_pretty(self) -> str:
        """返回格式化后的JSON字符串，便于调试。"""
        return self.model_dump_json(indent=2)


# --- 【核心新增】SectionBatch 模型 ---
class SectionBatch(BaseModel):
    """
    一个用于在角色之间批量传递 Section 对象的容器。
    A container for batch-passing Section objects between roles.
    """
    sections: List[Section]