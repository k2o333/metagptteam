# /root/metagpt/mgfr/metagpt_doc_writer/roles/__init__.py (最终精简版)

"""
This module provides the roles for the document writing team.
"""
from .base_role import DocWriterBaseRole
from .chief_pm import ChiefPM
from .scheduler_role import SchedulerRole
from .executor import Executor
from .performance_monitor import PerformanceMonitor
from .archiver import Archiver

__all__ = [
    "DocWriterBaseRole",
    "ChiefPM",
    "SchedulerRole",
    "Executor",
    "PerformanceMonitor",
    "Archiver",
]