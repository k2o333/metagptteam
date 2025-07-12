# 文件路径: /root/metagpt/mgfr/metagpt_doc_writer/roles/__init__.py (最终完整版)

"""
This module provides the roles for the document writing team.
By importing them here, we make them easily accessible from the package root.
"""

# 导入所有角色类，以便可以从 'metagpt_doc_writer.roles' 直接导入
from .archiver import Archiver
from .changeset_generator import ChangeSetGenerator
from .chief_pm import ChiefPM
from .doc_assembler import DocAssembler
from .doc_modifier import DocModifier
from .group_pm import GroupPM
from .performance_monitor import PerformanceMonitor
from .qa_agent import QAAgent
from .task_dispatcher import TaskDispatcher
from .task_refiner import TaskRefiner
from .technical_writer import TechnicalWriter

# 使用 __all__ 来定义当 'from metagpt_doc_writer.roles import *' 时会导出什么
# 这是一个好的编程实践
__all__ = [
    "Archiver",
    "ChangeSetGenerator",
    "ChiefPM",
    "DocAssembler",
    "DocModifier",
    "GroupPM",
    "PerformanceMonitor",
    "QAAgent",
    "TaskDispatcher",
    "TaskRefiner",
    "TechnicalWriter",
]