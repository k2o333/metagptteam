"""
This module provides the tools for the document writing team.
"""
from .base_tool import BaseTool, ToolSchema
from .web_search import WebSearch, WebSearchParams

__all__ = ["BaseTool", "ToolSchema", "WebSearch", "WebSearchParams"]
# /root/metagpt/mgfr/metagpt_doc_writer/tools/__init__.py

"""
This module provides the tools for the document writing team.
"""
from .base_tool import BaseTool, ToolSchema
from .web_search import WebSearch, WebSearchParams
from .diagram_generator import DiagramGenerator # 1. 新增导入

__all__ = [
    "BaseTool", 
    "ToolSchema", 
    "WebSearch", 
    "WebSearchParams",
    "DiagramGenerator", # 2. 新增导出
]