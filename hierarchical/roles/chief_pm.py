# hierarchical/roles/chief_pm.py
import sys
from pathlib import Path
from typing import Any

from metagpt.actions.add_requirement import UserRequirement
from metagpt.logs import logger
from metagpt.schema import Message
from hierarchical.actions import CreateSubOutline, Research
from hierarchical.roles.base_role import HierarchicalBaseRole
from hierarchical.schemas import Outline

class ChiefPM(HierarchicalBaseRole):
    name: str = "ChiefPM"
    profile: str = "Chief Product Manager"
    goal: str = "Create the initial high-level structure of the document."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([CreateSubOutline()]) # Research action is context-dependent
        self._watch([UserRequirement])
        self.plan_created = False

    def _get_action(self, action_class: type) -> Any:
        return next((a for a in self.actions if isinstance(a, action_class)), None)

    async def _act(self) -> Message:
        logger.info(f"--- {self.name} is acting... ---")

        if self.plan_created:
            logger.info(f"{self.name} has already created the plan. Idling.")
            return Message(content="Plan already created, idling.")

        latest_msg = self.get_memories(k=1)[0] if self.get_memories(k=1) else None
        cause_by_str = str(getattr(latest_msg, 'cause_by', None))
        if not latest_msg or "UserRequirement" not in cause_by_str:
            return Message(content="No user requirement found, idling.")

        outline: Outline = self.context.outline
        
        # 1. 执行研究 (用于AC3.1验收)
        logger.info("ChiefPM is conducting initial research...")
        research_action = Research(context=self.context)
        # 注意：这里我们让 Research 使用其默认LLM，不走资源池，因为它不是核心生成任务
        # 如果需要，也可以用 _execute_action(research_action, ...)
        research_result = await research_action.run(query=outline.goal, agent_type=self.name)
        logger.info(f"Initial research completed. Result snippet: {str(research_result)[:200]}...")

        # 2. 执行大纲创建
        create_outline_action = self._get_action(CreateSubOutline)
        
        # 【核心修改】使用我们新的执行器
        top_level_sections = await self._execute_action(
            create_outline_action, 
            parent_section=None, 
            goal=outline.goal
        )
        
        outline.root_sections = top_level_sections
        logger.info(f"Initial outline created with {len(top_level_sections)} top-level sections.")
        self.plan_created = True
        
        return Message(
            content="Initial outline created, ready for scheduling.",
            instruct_content=outline,
            role=self.profile,
            send_to="Scheduler"
        )