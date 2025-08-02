# mghier/hierarchical/roles/chief_pm.py (回归简洁与正确的最终版)

import sys
import json
from pathlib import Path
from typing import Any, Type

from metagpt.actions import Action
from metagpt.actions.add_requirement import UserRequirement
from metagpt.logs import logger
from metagpt.schema import Message

from hierarchical.actions import CreateSubOutline, Research 
from hierarchical.roles.base_role import HierarchicalBaseRole
from hierarchical.schemas import Outline
from hierarchical.rag.engines.docrag_engine import DocRAGEngine

class ChiefPM(HierarchicalBaseRole):
    name: str = "ChiefPM"
    profile: str = "Chief Product Manager"
    goal: str = "Create the initial high-level structure of the document."

    def __init__(self, **kwargs):
        # __init__ 方法非常干净，不依赖任何外部注入的 context
        super().__init__(**kwargs)
        self.set_actions([CreateSubOutline(), Research()])
        self._watch([UserRequirement])
        self.plan_created = False
        self.rag_engine_initialized = False # 新增一个标志位

    def _get_action(self, action_class: Type[Action]) -> Action:
        for action in self.actions:
            if isinstance(action, action_class):
                return action
        return None

    async def _initialize_rag_engine(self):
        """一个只执行一次的异步初始化方法"""
        if self.rag_engine_initialized:
            return

        research_action = self._get_action(Research)
        if not research_action:
            logger.error("Critical: Research action not found. Cannot initialize RAG.")
            self.rag_engine_initialized = True
            return

        # 在运行时从 self.context 中安全地读取配置
        persist_path = self.context.kwargs.get("custom_config", {}).get("docrag_persist_path")
        
        if persist_path:
            logger.info(f"ChiefPM is asynchronously creating DocRAGEngine from path: {persist_path}")
            docrag_engine = await DocRAGEngine.from_path(persist_path)
            research_action.set_docrag_engine(docrag_engine)
        else:
            logger.warning("docrag_persist_path not found in config. Research will not use internal RAG.")
            research_action.set_docrag_engine(None)

        self.rag_engine_initialized = True


    async def _act(self) -> Message:
        logger.info(f"--- {self.name} is acting... ---")

        # 【核心修复】在行动开始时，进行一次性的异步初始化
        await self._initialize_rag_engine()

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
        
        research_action = self._get_action(Research)
        
        research_results_by_query = await self._execute_action(
            research_action, 
            queries=[outline.goal]
        )
        
        research_context_for_outline = "No specific research context was gathered."
        research_result = research_results_by_query.get(outline.goal, {})
        
        if research_result.get("status") == "success":
            answer_data = research_result.get("final_answer") or research_result.get("raw_data")
            if isinstance(answer_data, (dict, list)):
                research_context_for_outline = json.dumps(answer_data, indent=2, ensure_ascii=False)
            else:
                research_context_for_outline = str(answer_data)
            logger.success(f"Research successful. Context for outlining:\n{research_context_for_outline[:300]}...")
        else:
            failure_reason = research_result.get("reason", "Engine not initialized")
            logger.warning(f"Research failed: {failure_reason}. Proceeding to generate outline without research context.")
        
        # --- Outline Creation Phase ---
        create_outline_action = self._get_action(CreateSubOutline)
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