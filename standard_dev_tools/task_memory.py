import uuid
import shutil
from pathlib import Path
from typing import List

from metagpt.logs import logger
from metagpt.memory.role_zero_memory import RoleZeroLongTermMemory
from metagpt.schema import Message


class TaskMemory:
    """
    为每个研究任务提供一个隔离的、临时的记忆系统，
    用于存储ReAct循环中的中间结果、思考过程和工具调用观察。
    它封装了一个临时的RoleZeroLongTermMemory实例，并在任务结束时自动清理。
    """

    def __init__(self, task_id: str = None, persist_path: str = "./.tmp_task_memories"):
        self.task_id = task_id or f"task_{uuid.uuid4().hex}"
        self.memory_path = Path(persist_path) / self.task_id
        
        # 动态实例化一个任务级别的记忆系统
        logger.info(f"Initializing task memory for task {self.task_id} at {self.memory_path}")
        self.task_memory = RoleZeroLongTermMemory(
            persist_path=str(self.memory_path),
            collection_name=self.task_id,
            # memory_k可以较低，因为我们希望观察结果尽快进入RAG
            memory_k=5 
        )

    def add(self, message: Message):
        """向记忆中添加一条消息（通常是观察结果）。"""
        self.task_memory.add(message)

    def get(self) -> List[Message]:
        """
        获取动态上下文/历史。
        RoleZeroLongTermMemory的get方法会自动结合短期记忆（最近的消息）
        和从RAG中检索出的相关长期记忆。
        """
        return self.task_memory.get()

    def clear(self):
        """在任务结束时清理临时记忆文件。"""
        if self.memory_path.exists():
            try:
                shutil.rmtree(self.memory_path)
                logger.info(f"Successfully cleaned up temporary task memory at {self.memory_path}")
            except OSError as e:
                logger.error(f"Error cleaning up task memory at {self.memory_path}: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clear()
