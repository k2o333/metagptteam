# hierarchical/roles/chief_pm.py (The Definitive Final Version)
import sys
from pathlib import Path
from typing import Any

from metagpt.actions import Action
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

    def __init__(self, **kwargs): # <--- SYNTAX ERROR FIXED
        super().__init__(**kwargs)
        self.set_actions([CreateSubOutline()]) 
        self._watch([UserRequirement])
        self.plan_created = False

    def _get_action(self, action_class: type) -> Action:
        """Helper to get an action instance by its class."""
        return next((a for a in self.actions if isinstance(a, action_class)), None)

    async def _act(self) -> Message:
        logger.info(f"--- {self.name} is acting... ---")

        if self.plan_created:
            logger.info(f"{self.name} has already created the plan. Idling permanently.")
            return None 

        user_req_msg_list = self.rc.memory.get_by_action(UserRequirement)
        if not user_req_msg_list:
             logger.warning(f"ChiefPM was triggered, but no UserRequirement found in memory. Skipping.")
             return None

        outline: Outline = self.context.outline

        # --- Research Phase (AC3.1) ---
        logger.info("ChiefPM is conducting initial research...")
        research_action = Research(context=self.context)
        research_result = await self._execute_action(
            research_action, 
            query=outline.goal, 
            agent_type=self.name
        )
        logger.info(f"Initial research completed. Result snippet: {str(research_result)[:200]}...")

        # --- Outline Creation Phase ---
        create_outline_action = self._get_action(CreateSubOutline)
        
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