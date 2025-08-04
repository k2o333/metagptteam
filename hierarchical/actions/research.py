# mghier/hierarchical/actions/research.py (阶段二: ReAct循环与任务记忆)

import sys
from pathlib import Path

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# -----------------

# 从拆分的模块导入
from .research_controller import Research

# 为了向后兼容，仍然导出Research类
__all__ = ["Research"]