"""
This module provides the roles for the document writing team.
"""
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