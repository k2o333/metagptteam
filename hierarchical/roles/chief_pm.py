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
        self.plan_created = False

    async def _act(self) -> Message:
        logger.info(f"--- {self.name} is acting... ---")

        if self.plan_created:
            logger.info(f"{self.name} has already created the plan. Idling.")
            return None

        # --- 【核心修正】从记忆中获取最新的消息，而不是依赖 rc.todo ---
        latest_msg = self.get_memories(k=1)[0] if self.get_memories(k=1) else None
        
        # 检查最新消息的起因是否是 UserRequirement
        cause_by_str = str(getattr(latest_msg, 'cause_by', None))
        if not latest_msg or "UserRequirement" not in cause_by_str:
            logger.warning(f"ChiefPM was triggered, but latest message in memory was not from UserRequirement. Skipping.")
            return None

        if not hasattr(self.context, 'outline') or not self.context.outline:
            logger.error("Outline object not found in context. Aborting.")
            return Message(content="Error: Outline not initialized.", role=self.profile)
        outline: Outline = self.context.outline
        
        # self.rc.todo 此时是框架决定要执行的 Action
        create_outline_action = self.rc.todo
        if not isinstance(create_outline_action, CreateSubOutline):
             logger.error(f"Expected CreateSubOutline action in rc.todo, but got {type(create_outline_action)}. Aborting.")
             return None
        
        # 传递 goal 给 action
        top_level_sections = await create_outline_action.run(parent_section=None, goal=outline.goal)

        outline.root_sections = top_level_sections
        logger.info(f"Initial outline created with {len(top_level_sections)} top-level sections.")

        self.plan_created = True
        
        return Message(
            content="Initial outline created, ready for scheduling.",
            instruct_content=outline,
            role=self.profile,
            send_to="Scheduler"
        )