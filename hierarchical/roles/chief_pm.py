# hierarchical/roles/chief_pm.py
import sys
from pathlib import Path

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# -----------------

from metagpt.schema import Message
from metagpt.logs import logger
from metagpt.actions.add_requirement import UserRequirement
from hierarchical.roles.base_role import HierarchicalBaseRole
from hierarchical.actions.create_sub_outline import CreateSubOutline
from hierarchical.schemas import Outline

class ChiefPM(HierarchicalBaseRole):
    """
    Strategic Planner Role.
    Receives a user idea and creates the initial top-level outline.
    """
    name: str = "ChiefPM"
    profile: str = "Chief Product Manager"
    goal: str = "Create the initial high-level structure of the document."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([CreateSubOutline])
        self._watch([UserRequirement]) 

    async def _act(self) -> Message:
        logger.info(f"--- {self.name} is acting... ---")
        
        messages = self.get_memories()
        if not messages:
            logger.warning(f"{self.name} has no messages in memory. Skipping.")
            return None
        
        latest_msg = messages[-1]
        
        # --- 【核心修正】采纳官方建议，使用更健壮的字符串检查 ---
        # 添加详细的调试日志
        cause_by_val = getattr(latest_msg, 'cause_by', None)
        logger.debug(f"ChiefPM received message with cause_by: {cause_by_val} (type: {type(cause_by_val)})")

        # 将 cause_by 转换为字符串进行检查，这样更可靠
        cause_by_str = str(cause_by_val)
        if "UserRequirement" not in cause_by_str:
            logger.warning(f"Latest message for {self.name} was not caused by 'UserRequirement'. Skipping. (cause_by was: '{cause_by_str}')")
            return None

        # 从自定义的 context 中获取全局唯一的 Outline 对象
        if not hasattr(self.context, 'outline') or not self.context.outline:
            logger.error("Outline object not found in context. Aborting.")
            return Message(content="Error: Outline not initialized.", role=self.profile)
        outline: Outline = self.context.outline
        
        create_outline_action = self.rc.todo
        if not isinstance(create_outline_action, CreateSubOutline):
             logger.error(f"Expected CreateSubOutline action, but got {type(create_outline_action)}. Aborting.")
             return None

        top_level_sections = await create_outline_action.run(parent_section=None)

        outline.root_sections = top_level_sections
        logger.info(f"Initial outline created with {len(top_level_sections)} top-level sections.")

        return Message(
            content="Initial outline created, ready for scheduling.",
            instruct_content=outline,
            role=self.profile,
            send_to="Scheduler"
        )