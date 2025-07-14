# /root/metagpt/mgfr/metagpt_doc_writer/roles/chief_pm.py (修正版)

from .base_role import DocWriterBaseRole
from metagpt.schema import Message
from metagpt_doc_writer.actions.create_plan import CreatePlan
# 修正：移除对 CustomUserRequirement 的导入，因为它不存在
from metagpt_doc_writer.schemas.doc_structures import Plan
from metagpt.logs import logger

class ChiefPM(DocWriterBaseRole):
    name: str = "ChiefPM"
    profile: str = "Chief Product Manager"
    goal: str = "Receive user requirements and create a detailed, executable plan."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([CreatePlan()])

    # run方法现在是它的主要入口，而不是_act
    async def run(self, user_req_msg: Message) -> Message:
        logger.info(f"{self.name} is creating a plan from user requirement...")
        
        # 直接从消息内容获取目标
        goal = user_req_msg.content
        if not goal:
            logger.error("User requirement message has no content. Aborting plan creation.")
            # 返回一个表示错误的消息或None
            return Message(content="Error: Empty user requirement.")

        plan: Plan = await self.actions[0].run(goal=goal)
        
        return Message(
            content=f"Plan created for goal: '{goal}' with {len(plan.tasks)} tasks.", 
            instruct_content=plan,
            role=self.profile,
            cause_by=type(self.actions[0])
        )