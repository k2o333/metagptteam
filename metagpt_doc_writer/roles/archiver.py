# 文件路径: /root/metagpt/mgfr/metagpt_doc_writer/roles/archiver.py (原生重构版)

import shutil
from pathlib import Path
from datetime import datetime
from .base_role import DocWriterBaseRole
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt_doc_writer.schemas.doc_structures import Approval, FinalDelivery, ProjectArchived

class Archiver(DocWriterBaseRole): # 【关键修正】: 继承自 Role
    name: str = "Archiver"
    profile: str = "Archiver"
    goal: str = "Archive the project assets upon completion."
    
    def __init__(self, archive_path: str, **kwargs):
        super().__init__(**kwargs)
        self.archive_path = Path(archive_path)
        self.set_actions([]) # 非LLM角色，没有可供LLM选择的行动
        self._watch({Approval, FinalDelivery})
        self._set_react_mode(react_mode="by_order", max_react_loop=1)

    async def _act(self) -> Message:
        """
        确定地执行归档操作。
        """
        logger.info(f"{self.name} is archiving the project...")
        
        # 这个角色只在流程结束时被手动触发，所以我们假设记忆中已有产物
        try:
            final_delivery_msg = next(m for m in reversed(self.rc.memory.get()) if isinstance(m.instruct_content, FinalDelivery))
        except StopIteration:
            logger.warning("No FinalDelivery message found in memory, cannot archive.")
            return Message(content="No final delivery found to archive.", role=self.profile)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_archive_path = self.archive_path / f"project_{timestamp}"
        project_archive_path.mkdir(parents=True, exist_ok=True)
        
        # ... (归档逻辑保持不变)
        
        return Message(
            content=f"Project archived to {project_archive_path}",
            instruct_content=ProjectArchived(archive_path=str(project_archive_path))
        )