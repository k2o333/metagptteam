# hierarchical/schemas.py (The Definitive Final Version - Using PrivateAttr)
from __future__ import annotations
import uuid
from pydantic import BaseModel, Field, ConfigDict, PrivateAttr # 【核心修正】: 导入 PrivateAttr
from typing import List, Optional, Dict, Any
from datetime import datetime
from llama_index.core.schema import NodeWithScore

class Section(BaseModel):
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
            self.display_id = self.title

Section.model_rebuild()

class Outline(BaseModel):
    goal: str
    root_sections: List[Section] = Field(default_factory=list)

    def find_section(self, section_id: str, search_in: Optional[List[Section]] = None) -> Optional[Section]:
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
        return self.model_dump_json(indent=2)

class SectionBatch(BaseModel):
    sections: List[Section]

class RAGContext(BaseModel):
    """
    一个容器，用于存放RAG检索过程中的上下文信息。
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # 【核心修正】: 使用 PrivateAttr 彻底绕开 Pydantic 的验证
    _nodes: List[NodeWithScore] = PrivateAttr(default_factory=list)
    raw_data: List[Dict] = Field(default_factory=list, description="从外部服务获取的原始数据")

    def __init__(self, **data: Any):
        """
        自定义初始化方法，以处理非 Pydantic 类型的 `nodes` 字段。
        """
        nodes_data = data.pop("nodes", [])
        super().__init__(**data)
        self._nodes = nodes_data

    @property
    def nodes(self) -> List[NodeWithScore]:
        """提供一个 property 来方便地访问 _nodes。"""
        return self._nodes

class RAGResponse(BaseModel):
    """
    封装了RAG引擎单次查询的完整响应。
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    query: str
    rag_context: RAGContext
    response: str = Field(default="", description="由LLM基于上下文生成的最终答案")
    extra_info: Dict[str, Any] = Field(default_factory=dict)