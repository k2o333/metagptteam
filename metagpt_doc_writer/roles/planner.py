# 路径: /root/metagpt/mgfr/metagpt_doc_writer/roles/planner.py (最终版)
from .base_role import DocWriterBaseRole
from metagpt.schema import Message
from metagpt.actions.add_requirement import UserRequirement
from metagpt_doc_writer.actions.create_plan import CreatePlan
from metagpt_doc_writer.schemas.doc_structures import Plan
from metagpt.logs import logger

class Planner(DocWriterBaseRole):
    name: str = "Planner"
    profile: str = "Master Planner"
    goal: str = "Decompose a user's requirement into a detailed, executable plan."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([CreatePlan()])
        self._watch({UserRequirement}) # 只对最初的用户需求做出反应
        self.planned = False

    async def _act(self) -> Message:
        if self.planned:
            return None # 已经规划过，不再行动

        logger.info(f"{self.name} is creating a plan...")
        user_requirement = self.rc.news[0].content
        plan: Plan = await self.actions[0].run(user_requirement)
        
        self.planned = True
        
        # 将Plan作为instruct_content发布，让SchedulerRole监听
        return Message(content=f"Plan created with {len(plan.tasks)} tasks.", instruct_content=plan)