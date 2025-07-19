# hierarchical/context.py
import asyncio
from typing import Dict, Any, Optional

from metagpt.context import Context as BaseContext
from hierarchical.schemas import Outline
from pydantic import Field

class HierarchicalContext(BaseContext):
    """
    自定义Context，通过Pydantic字段来安全地存储不可序列化的运行时对象。
    """
    
    # 【核心修正】将 outline 和 semaphore 定义为 Pydantic 字段。
    # 使用 Optional[...] 和 default=None 来表示它们可以为空。
    # 使用 exclude=True 来告诉Pydantic在序列化（如model_dump）时忽略这些字段。
    outline: Optional[Outline] = Field(default=None, exclude=True)
    semaphore: Optional[asyncio.Semaphore] = Field(default=None, exclude=True)

    # 我们不再需要重写 serialize 方法，因为 exclude=True 已经处理了这个问题。
    # 父类的 serialize 方法现在可以安全地工作了。