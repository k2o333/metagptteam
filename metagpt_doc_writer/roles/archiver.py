# /root/metagpt/mgfr/metagpt_doc_writer/roles/archiver.py (修正版)

import shutil
from pathlib import Path
from datetime import datetime
import json
from .base_role import DocWriterBaseRole
from metagpt.logs import logger
# 【核心修正】移除对 ProjectArchived 的导入
from metagpt_doc_writer.schemas.doc_structures import FinalDelivery

class Archiver(DocWriterBaseRole):
    name: str = "Archiver"
    profile: str = "Archiver"
    goal: str = "Archive the project assets upon completion."
    
    def __init__(self, archive_path: str, **kwargs):
        super().__init__(**kwargs)
        self.archive_path = Path(archive_path)
        self.set_actions([])
        self._watch({})

    async def archive(self, final_doc_path: str, all_tasks: dict, plan: dict) -> bool:
        """
        一个独立的归档方法，由外部调度器在流程结束时调用。
        """
        logger.info(f"{self.name} is archiving the project...")
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_archive_path = self.archive_path / f"project_{timestamp}"
            project_archive_path.mkdir(parents=True, exist_ok=True)
            
            # 1. 归档最终文档
            if final_doc_path and Path(final_doc_path).exists():
                shutil.copy(final_doc_path, project_archive_path)
                logger.info(f"Archived final document: {final_doc_path}")

            # 2. 归档计划和任务结果
            serializable_tasks = {tid: task.model_dump() for tid, task in all_tasks.items()}
            archive_data = {
                "plan": plan.model_dump(),
                "completed_tasks": serializable_tasks
            }
            with open(project_archive_path / "plan_and_results.json", "w", encoding='utf-8') as f:
                json.dump(archive_data, f, indent=4)
            logger.info("Archived plan and task results.")

            logger.success(f"Project successfully archived to: {project_archive_path}")
            # 【核心修正】返回一个简单的布尔值表示成功
            return True
        except Exception as e:
            logger.error(f"Archiving failed: {e}", exc_info=True)
            return False