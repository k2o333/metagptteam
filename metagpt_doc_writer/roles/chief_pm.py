# 路径: /root/metagpt/mgfr/metagpt_doc_writer/roles/chief_pm.py (修复后全文)

from metagpt.schema import Message
from metagpt.actions.add_requirement import UserRequirement
from metagpt.logs import logger

from metagpt_doc_writer.actions.review_and_command import ReviewAndCommand
from metagpt_doc_writer.schemas.doc_structures import (
    FullDraft, 
    RefinedTask, 
    ApprovedTask, 
    ProjectPlan
)
from .base_role import MyBaseRole

class ChiefPM(MyBaseRole):
    name: str = "ChiefPM"
    profile: str = "Chief Product Manager"
    goal: str = "Oversee the entire document generation process and ensure final quality."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # ChiefPM的核心动作是审阅，但它也负责启动项目和审批任务。
        # _think方法会根据上下文选择最合适的动作，这里只有一个，所以总是会选它。
        self.set_actions([ReviewAndCommand])
        # 监听用户需求、待审批任务和完整草稿
        self._watch({UserRequirement, FullDraft, RefinedTask})

    async def _act(self) -> Message:
        """
        根据当前状态决定ChiefPM的具体行动：
        1. 如果有完整草稿，进行审阅。
        2. 如果没有草稿但有待审批任务，进行审批。
        3. 如果以上皆无但有初始用户需求，则创建项目计划。
        4. 如果以上皆无，则暂时等待。
        """
        
        # 获取当前要执行的动作，它是由 _think 方法决定的
        todo = self.rc.todo
        if not todo:
            logger.warning(f"{self.name} has no action to perform. Waiting for new messages.")
            return Message(content="No tasks to perform.", role=self.profile)

        memories = self.get_memories()

        # 优先级1：审阅完整草稿
        full_draft_msgs = [m for m in memories if isinstance(m.instruct_content, FullDraft)]
        if full_draft_msgs:
            # 只有当待办事项是ReviewAndCommand时才审阅
            if isinstance(todo, ReviewAndCommand):
                logger.info(f"{self.name} is reviewing a full draft.")
                full_draft_msg = full_draft_msgs[-1]
                review_notes = await todo.run(full_draft_msg.instruct_content)
                return Message(content="Review notes generated", instruct_content=review_notes, cause_by=type(todo))
            else:
                 logger.warning(f"{self.name} received a FullDraft but the next action is not ReviewAndCommand. Current action: {todo.name}. Waiting.")

        # 优先级2：审批细化后的任务
        refined_task_msgs = [m for m in memories if isinstance(m.instruct_content, RefinedTask)]
        if refined_task_msgs:
            approved_task_msgs = [m for m in memories if isinstance(m.instruct_content, ApprovedTask)]
            latest_refined_task = refined_task_msgs[-1].instruct_content
            
            # 检查这个任务是否已经被审批过
            is_approved = any(
                t.instruct_content.chapter_title == latest_refined_task.chapter_title 
                for t in approved_task_msgs
            )
            
            if not is_approved:
                logger.info(f"{self.name} is approving a refined task: '{latest_refined_task.chapter_title}'")
                approved_task = ApprovedTask(
                    chapter_title=latest_refined_task.chapter_title,
                    refined_task=latest_refined_task
                )
                # 使用 todo (ReviewAndCommand) 作为 cause_by，表示这是在审阅流程中发生的
                return Message(content="Task approved", instruct_content=approved_task, cause_by=type(todo))

        # 优先级3：处理初始用户需求，创建项目计划
        user_req_msgs = [m for m in memories if m.cause_by == UserRequirement]
        if user_req_msgs:
            project_plan_msgs = [m for m in memories if isinstance(m.instruct_content, ProjectPlan)]
            if not project_plan_msgs:
                user_req_msg = user_req_msgs[-1]
                logger.info(f"{self.name} is processing the initial user requirement to create a project plan.")
                # 这里可以调用一个专门的Action来生成更智能的plan，但暂时先硬编码
                project_plan = ProjectPlan(modules=[f"Module 1 for '{user_req_msg.content}'", "Module 2 for Conclusion"])
                return Message(content="Project plan created.", instruct_content=project_plan, cause_by=type(todo))

        # 如果以上条件都不满足，说明真的没事可做
        logger.warning(f"{self.name} has nothing to do at this moment.")
        return Message(content="No tasks to perform.", role=self.profile)