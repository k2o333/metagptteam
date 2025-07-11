# 路径: /root/metagpt/mgfr/metagpt_doc_writer/roles/chief_pm.py (最终修复版)

from metagpt.schema import Message
from metagpt.logs import logger

# 移除所有不必要的导入
from metagpt_doc_writer.actions.review_and_command import ReviewAndCommand
from metagpt_doc_writer.schemas.doc_structures import FullDraft, ReviewNotes
from .base_role import MyBaseRole

class ChiefPM(MyBaseRole):
    name: str = "ChiefPM"
    profile: str = "Chief Product Manager"
    goal: str = "Oversee the entire document generation process and ensure final quality."
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([ReviewAndCommand()])
        # 只监听它真正需要处理的消息
        self._watch({FullDraft})

    async def _act(self) -> Message:
        """
        审阅最新的 FullDraft 并生成 ReviewNotes。
        这个版本更纯粹，只处理审阅任务。
        """
        logger.info(f"Executing action: {self.name} for reviewing.")
        
        memories = self.get_memories()
        try:
            full_draft_msg = next(m for m in reversed(memories) if isinstance(m.instruct_content, FullDraft))
        except StopIteration:
            logger.warning("No FullDraft found in memory for review. Nothing to do.")
            return None

        review_action = self.actions[0]
        if not isinstance(review_action, ReviewAndCommand):
            logger.error(f"Action setup error: Expected ReviewAndCommand, found {type(review_action)}.")
            return None
            
        review_notes = await review_action.run(full_draft_msg.instruct_content)
        
        return Message(content="Review notes generated.", instruct_content=review_notes)