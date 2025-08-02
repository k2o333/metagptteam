# mghier/hierarchical/actions/complete_all_tasks.py (修复版)

import sys
from pathlib import Path

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# -----------------

from metagpt.actions import Action
from metagpt.logs import logger

class CompleteAllTasks(Action):
    """
    A specific action used by Scheduler to signal that all document generation tasks are completed.
    This action is meant to be watched by roles like Archiver.
    """
    name: str = "CompleteAllTasks"
    
    # 【核心修复】在 run 方法签名中添加 **kwargs
    async def run(self, **kwargs) -> str:
        """
        This action doesn't perform any complex logic, it simply signals completion.
        It now accepts **kwargs to ignore any extra parameters.
        """
        logger.info("Signaling: ALL_DOCUMENT_TASKS_COMPLETED.")
        return "ALL_DOCUMENT_TASKS_COMPLETED"