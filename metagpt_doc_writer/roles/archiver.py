# /root/metagpt/mgfr/metagpt_doc_writer/roles/archiver.py

from .base_role import MyBaseRole
from pathlib import Path
from metagpt.logs import logger
import shutil

class Archiver(MyBaseRole):
    name: str = "Archiver"
    profile: str = "Archiver"
    goal: str = "Archive the project assets upon completion"

    def __init__(self, archive_path: str = "./archive", **kwargs):
        super().__init__(**kwargs)
        self.archive_path = Path(archive_path)
        self.set_actions([]) # Non-LLM role

    async def _act(self) -> None:
        """
        Archives the project outputs. This is a simplified placeholder.
        A real implementation would be more complex.
        """
        logger.info(f"Archiving project to {self.archive_path}...")
        
        # 假设最终产物在 workspace 目录
        workspace_path = Path("./workspace") 
        if not workspace_path.exists():
            logger.warning(f"Workspace path '{workspace_path}' not found. Nothing to archive.")
            return

        # 创建归档目录
        self.archive_path.mkdir(parents=True, exist_ok=True)
        
        # 简单的复制逻辑
        try:
            # For demonstration, copy the entire workspace. A real implementation would be more selective.
            shutil.copytree(workspace_path, self.archive_path / workspace_path.name, dirs_exist_ok=True)
            logger.info("Archiving successful.")
        except Exception as e:
            logger.error(f"Archiving failed: {e}")