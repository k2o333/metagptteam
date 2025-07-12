# /root/metagpt/mgfr/metagpt_doc_writer/roles/group_pm.py

from metagpt.actions import Action, UserRequirement
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt.utils.common import OutputParser
from .base_role import DocWriterBaseRole
from metagpt_doc_writer.schemas.doc_structures import ProjectPlan, ModuleOutline
from .chief_pm import DecomposeTopic # 导入 DecomposeTopic 的 Action 用于 watch

class CreateModuleOutline(Action):
    name: str = "CreateModuleOutline"
    async def run(self, module_title: str, topic: str, use_llm: bool = False) -> ModuleOutline:
        if not use_llm:
            logger.warning(f"CreateModuleOutline is using MOCK data for '{module_title}'.")
            return ModuleOutline(module_title=module_title, chapters=[f"{module_title} - Mock Chapter 1", f"{module_title} - Mock Chapter 2"])

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
        self.set_actions([CreateModuleOutline()]) # 实例化Action
        self._watch({DecomposeTopic}) # 直接watch Action类，更可靠
        self._set_react_mode(react_mode="by_order", max_react_loop=1)

    async def _act(self) -> Message:
        if not self.rc.todo: return None
        action = self.rc.todo
        logger.info(f"{self._setting}: ready to {action.name}")
        
        # The trigger message should contain the ProjectPlan
        trigger_msg = self.rc.history[-1] 
        project_plan = trigger_msg.instruct_content
        topic = trigger_msg.content # Original topic comes from the content of UserRequirement, propagated by ChiefPM

        if not isinstance(project_plan, ProjectPlan):
            logger.warning(f"GroupPM: Expected ProjectPlan, but got {type(project_plan)}. Skipping.")
            return None

        if not topic:
             logger.error("GroupPM: Original topic is empty in trigger message from ChiefPM. Aborting module outline creation.")
             return None

        use_llm = self.llm_activation.get(action.name, False)
        
        # Iterate over modules and create outlines
        for module_title in project_plan.modules:
            outline = await action.run(module_title=module_title, topic=topic, use_llm=use_llm)
            
            # publish_message to the environment for other roles to observe
            self.rc.env.publish_message(Message(content=topic, instruct_content=outline, role=self.profile, cause_by=type(action).__name__))
            logger.debug(f"GroupPM: Published ModuleOutline for '{outline.module_title}'.")
        
        logger.info(f"GroupPM: Finished creating and publishing outlines for all modules. Returning None.")
        # Returning None indicates that this role has completed its immediate task and published its results
        # directly to the environment. The Team's main loop will pick up these published messages.
        return None