# /root/metagpt/mgfr/metagpt_doc_writer/roles/technical_writer.py (修正并简化)

from .base_role import DocWriterBaseRole
from metagpt.schema import Message
from metagpt.logs import logger
from typing import Optional

# 导入真正的 Action 和 Schema
from metagpt_doc_writer.actions.write_section import WriteSection
from metagpt_doc_writer.schemas.doc_structures import ApprovedTask

# 关键修正：不再从 chief_pm 导入，因为 ApproveTask 已经不在那里了
# from .chief_pm import ApproveTask  <-- 删除这一行

class TechnicalWriter(DocWriterBaseRole):
    name: str = "TechnicalWriter"
    profile: str = "Technical Writer"
    goal: str = "Write high-quality, clear, and accurate technical documentation sections."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([WriteSection()])
        # 在我们的新架构中，这个角色其实不被直接使用。
        # 为了让文件能被导入，我们让它监听一个它之前依赖的类型。
        self._watch({ApprovedTask})
        self._set_react_mode(react_mode="by_order", max_react_loop=1)

    async def _act(self) -> Message:
        if not self.rc.todo: return None
        action = self.rc.todo
        logger.info(f"{self._setting}: ready to {action.name}")
        
        approved_task_msg = self.rc.history[-1]
        if not isinstance(approved_task_msg.instruct_content, ApprovedTask):
            return None

        draft_section = await action.run(approved_task_msg.instruct_content)
        return Message(content=draft_section.content, instruct_content=draft_section, cause_by=type(action))