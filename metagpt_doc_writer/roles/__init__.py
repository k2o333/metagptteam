# 路径: /root/metagpt/mgfr/metagpt_doc_writer/roles/__init__.py (已修复)

"""
This module provides the roles for the document writing team.
"""
# To prevent circular imports, we list the role names here for discoverability,
# but we do NOT import them directly. The calling code should import from the
# specific module, e.g., 'from metagpt_doc_writer.roles.chief_pm import ChiefPM'.

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
    "Planner",         # 从旧文件里找到的，也加上
    "SchedulerRole",   # 从旧文件里找到的，也加上
]