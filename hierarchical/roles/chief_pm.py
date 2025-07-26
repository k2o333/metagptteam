# mghier/hierarchical/roles/chief_pm.py (第二次修复版)

import sys
import json
from pathlib import Path
from typing import Any, Type # 【新增】导入 Type

from metagpt.actions import Action
from metagpt.actions.add_requirement import UserRequirement
from metagpt.logs import logger
from metagpt.schema import Message
# 【修改】导入Action类本身
from hierarchical.actions import CreateSubOutline, Research 
from hierarchical.roles.base_role import HierarchicalBaseRole
from hierarchical.schemas import Outline

class ChiefPM(HierarchicalBaseRole):
    name: str = "ChiefPM"
    profile: str = "Chief Product Manager"
    goal: str = "Create the initial high-level structure of the document."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 【核心修复】传递 Action 类，而不是实例
        self.set_actions([CreateSubOutline, Research]) 
        self._watch([UserRequirement])
        self.plan_created = False

    # 【修改】_get_action 方法现在通过类的类型来查找实例
    def _get_action(self, action_class: Type[Action]) -> Action:
        """
        Helper to get an action instance by its class type.
        Role.actions 列表中存放的是Action的实例。
        """
        # self.actions 列表是在 super().__init__ 中由 set_actions 创建的，里面存放的是实例
        for action in self.actions:
            if isinstance(action, action_class):
                return action
        return None

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

        # --- Research Phase ---
        logger.info("ChiefPM is conducting initial research...")
        
        # 【修改】通过类来获取Action实例
        research_action = self._get_action(Research)
        if not research_action:
            raise RuntimeError("Research action not found in ChiefPM.")
        
        # 不再需要手动注入context，因为Role在初始化时已经做了
        # research_action.context = self.context 
        
        research_results_by_query = await self._execute_action(
            research_action, 
            queries=[outline.goal]
        )
        
        research_context_for_outline = "No specific research context was gathered."
        research_result = research_results_by_query.get(outline.goal, {})
        
        if research_result.get("status") == "success":
            answer_data = research_result.get("final_answer") or research_result.get("data")
            if isinstance(answer_data, (dict, list)):
                research_context_for_outline = json.dumps(answer_data, indent=2, ensure_ascii=False)
            else:
                research_context_for_outline = str(answer_data)
            logger.success(f"Research successful. Context for outlining:\n{research_context_for_outline[:300]}...")
        else:
            failure_reason = research_result.get("reason", "Unknown reason")
            logger.warning(f"Research failed: {failure_reason}. Proceeding to generate outline without research context.")
        
        # --- Outline Creation Phase ---
        # 【修改】通过类来获取Action实例
        create_outline_action = self._get_action(CreateSubOutline)
        if not create_outline_action:
            raise RuntimeError("CreateSubOutline action not found in ChiefPM.")
            
        top_level_sections = await self._execute_action(
            create_outline_action, 
            parent_section=None, 
            goal=outline.goal,
            research_context=research_context_for_outline
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