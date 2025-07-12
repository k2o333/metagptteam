# /root/metagpt/mgfr/metagpt_doc_writer/roles/technical_writer.py (最终完整配置驱动版)

from .base_role import DocWriterBaseRole
from metagpt.schema import Message
from metagpt.logs import logger
from typing import Optional

from metagpt_doc_writer.actions.write_section import WriteSection
from metagpt_doc_writer.schemas.doc_structures import ApprovedTask, DraftSection
from metagpt_doc_writer.mcp.manager import MCPManager
from .chief_pm import ApproveTask

class TechnicalWriter(DocWriterBaseRole):
    name: str = "TechnicalWriter"
    profile: str = "Technical Writer"
    goal: str = "Write high-quality, clear, and accurate technical documentation sections."

    def __init__(self, mcp_manager: Optional[MCPManager] = None, **kwargs):
        super().__init__(**kwargs)
        # 将 use_llm 开关传递给 Action
        use_llm = self.llm_activation.get(WriteSection.__name__, False)
        self.set_actions([WriteSection(mcp_manager=mcp_manager, use_llm=use_llm)])
        self._watch({f"{ApproveTask.__module__}.{ApproveTask.__name__}"})
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