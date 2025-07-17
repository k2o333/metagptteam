# /root/metagpt/mgfr/metagpt_doc_writer/actions/__init__.py

from .create_plan import CreatePlan
from .research import Research
from .write import Write
from .review import Review
from .finalize import FinalizeDocument
# 【核心修正】: 移除对已删除的 reflect.py 文件的导入
# from .reflect import ReflectAndOptimize
# 【核心修正】: 新增对我们新创建的 revise.py 文件的导入
from .revise import Revise

__all__ = [
    "CreatePlan",
    "Research",
    "Write",
    "Review",
    "FinalizeDocument",
    "Revise", # 【核心修正】: 将Revise加入__all__
]