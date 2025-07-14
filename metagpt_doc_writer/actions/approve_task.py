# /root/metagpt/mgfr/metagpt_doc_writer/actions/approve_task.py (已修正)

from metagpt.actions import Action
from metagpt.logs import logger
# --- 修正: 使用绝对路径导入 ---
from mgfr.metagpt_doc_writer.schemas.doc_structures import ApprovedTask, RefinedTask

class ApproveTask(Action):
    name: str = "ApproveTask"
    async def run(self, refined_task: RefinedTask) -> ApprovedTask:
        logger.info(f"Action: Approving task '{refined_task.chapter_title}'...")
        return ApprovedTask(chapter_title=refined_task.chapter_title, refined_task=refined_task)