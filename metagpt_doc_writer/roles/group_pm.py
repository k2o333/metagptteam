# /root/metagpt/mgfr/metagpt_doc_writer/roles/group_pm.py (最终简化版)

import asyncio
from metagpt.actions import Action
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt.utils.common import OutputParser
from .base_role import DocWriterBaseRole
from metagpt_doc_writer.schemas.doc_structures import ProjectPlan, ModuleOutline

class CreateModuleOutline(Action):
    # Action定义保持不变
    name: str = "CreateModuleOutline"
    async def run(self, module_title: str, topic: str, use_llm: bool = False) -> ModuleOutline:
        if not use_llm:
            logger.warning(f"CreateModuleOutline is using MOCK data for '{module_title}'.")
            return ModuleOutline(module_title=module_title, chapters=[f"{module_title} - Mock Chapter 1", f"{module_title} - Mock Chapter 2"])
        # ... (LLM 调用逻辑不变)
        logger.info(f"Action: Creating outline for module '{module_title}' on topic '{topic}' with LLM...")
        prompt = f"""
        You are an expert curriculum designer. For a document about "{topic}", create a chapter outline for the module: "{module_title}".
        Generate 2-4 key chapter titles.
        Respond ONLY with a valid JSON object: {{"module_title": "...", "chapters": ["...", "..."]}}
        """
        response_str = await self._aask(prompt)
        try:
            data_dict = OutputParser.parse_code(text=response_str, lang="json")
            if isinstance(data_dict, str):
                import json
                data_dict = json.loads(data_dict)
            return ModuleOutline(**data_dict)
        except Exception as e:
            logger.error(f"Failed to parse LLM for CreateModuleOutline: {e}\nRaw response:\n{response_str}")
            return ModuleOutline(module_title=module_title, chapters=["Chapter 1 (Parsing Error)"])

class GroupPM(DocWriterBaseRole):
    name: str = "GroupPM"
    profile: str = "Group Product Manager"
    goal: str = "Break down high-level project modules into detailed chapter outlines."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([CreateModuleOutline()])
        self._watch({ProjectPlan})
        self._set_react_mode(react_mode="by_order", max_react_loop=1)

    async def _act(self) -> Message:
        if not self.rc.todo: return None
        action = self.rc.todo
        logger.info(f"{self._setting}: ready to {action.name}")
        
        trigger_msg = self.rc.history[-1] 
        project_plan = trigger_msg.instruct_content
        topic = trigger_msg.content

        if not isinstance(project_plan, ProjectPlan): return None
        if not topic: return None

        use_llm = self.llm_activation.get(action.name, False)
        
        tasks = [action.run(module_title=module_title, topic=topic, use_llm=use_llm) for module_title in project_plan.modules]
        outlines = await asyncio.gather(*tasks)
        
        if not outlines: return None

        logger.info(f"GroupPM generated {len(outlines)} outlines. Sending to Scheduler.")
        
        # 【核心修改】将包含列表的消息直接发送给 Scheduler
        return Message(
            content=f"Dispatching {len(outlines)} module outlines for scheduling.",
            instruct_content=outlines,
            role=self.profile,
            cause_by=type(action).__name__,
            send_to="Scheduler" # 明确指定接收者
        )