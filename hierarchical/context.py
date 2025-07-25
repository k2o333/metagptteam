# mghier/hierarchical/context.py (修改版)

import asyncio
from typing import Dict, Any, Optional

from metagpt.context import Context as BaseContext
from pydantic import Field
from hierarchical.schemas import Outline

# 【新增】导入 MCPManager
from mcp.manager import MCPManager 

class HierarchicalContext(BaseContext):
    """
    自定义Context，通过Pydantic字段来安全地存储不可序列化的运行时对象。
    """
    outline: Optional[Outline] = Field(default=None, exclude=True)
    semaphore: Optional[asyncio.Semaphore] = Field(default=None, exclude=True)
    
    # 【新增】为 MCPManager 添加字段
    mcp_manager: Optional[MCPManager] = Field(default=None, exclude=True)