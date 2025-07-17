# /root/metagpt/mgfr/metagpt_doc_writer/roles/chief_pm.py

from .base_role import DocWriterBaseRole
from metagpt.schema import Message
from metagpt.actions.add_requirement import UserRequirement
# 【核心修正】导入RoleReactMode枚举
from metagpt.roles.role import RoleReactMode
from metagpt_doc_writer.actions.create_plan import CreatePlan
from metagpt_doc_writer.schemas.doc_structures import Plan
from metagpt.logs import logger

class ChiefPM(DocWriterBaseRole):
    name: str = "ChiefPM"
    profile: str = "Chief Product Manager"
    goal: str = "Receive user requirements and create a detailed, executable plan."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # set_actions 会自动处理 context 和 llm 的注入
        self.set_actions([CreatePlan()])
        
    # ChiefPM的角色非常简单，甚至不需要复杂的react_mode，
    # 但为了规范，我们保留一个简单的模式。
    # run方法是其主要入口。
    async def run(self, user_req_msg: Message) -> Message:
        logger.info(f"{self.name} is creating a plan from user requirement...")
        
        goal = user_req_msg.content
        if not goal:
            logger.error("User requirement message has no content. Aborting plan creation.")
            return Message(content="Error: Empty user requirement.")

        # self.actions[0] 就是CreatePlan的实例
        plan: Plan = await self.actions[0].run(goal=goal)
        
        return Message(
            content=f"Plan created for goal: '{goal}' with {len(plan.tasks)} tasks.", 
            instruct_content=plan,
            role=self.profile,
            cause_by=type(self.actions[0])
        )