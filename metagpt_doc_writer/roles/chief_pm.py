# /root/metagpt/mgfr/metagpt_doc_writer/roles/chief_pm.py (已修改)

from metagpt.actions import Action, UserRequirement
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt.utils.common import OutputParser
from .base_role import DocWriterBaseRole
from metagpt_doc_writer.schemas.doc_structures import (
    ProjectPlan, RefinedTask, ApprovedTask, FullDraft, QAReport, ReviewNotes, Approval
)
from metagpt_doc_writer.actions.review_and_command import ReviewAndCommand

class DecomposeTopic(Action):
    name: str = "DecomposeTopic"
    async def run(self, topic: str, use_llm: bool = False) -> ProjectPlan:
        if not use_llm:
            logger.warning(f"DecomposeTopic is using MOCK data for '{topic}'.")
            return ProjectPlan(modules=[f"Mocked Module 1 for '{topic}'", "Mocked Module 2"])

        logger.info(f"Action: Decomposing topic '{topic}' with LLM...")
        prompt = f"""
        As an expert project manager, your task is to break down a user's high-level requirement into a logical, top-level project plan for a comprehensive technical document.
        User Requirement: "{topic}"
        Generate a list of 3-5 main module titles.
        Your response MUST be a single, valid JSON object containing only one key: "modules".
        Example: {{"modules": ["1. Introduction", "2. Core Concepts", "3. Advanced Topics", "4. Conclusion"]}}
        """
        response_str = await self._aask(prompt)
        try:
            data_dict = OutputParser.parse_code(text=response_str, lang="json")
            if isinstance(data_dict, str):
                import json
                data_dict = json.loads(data_dict)
            logger.info(f"LLM generated modules: {data_dict.get('modules')}")
            return ProjectPlan(**data_dict)
        except Exception as e:
            logger.error(f"Failed to parse LLM response for DecomposeTopic: {e}\nRaw response:\n{response_str}")
            return ProjectPlan(modules=[f"Default Plan for '{topic}' due to parsing error."])

class ApproveTask(Action):
    name: str = "ApproveTask"
    async def run(self, refined_task: RefinedTask) -> ApprovedTask:
        logger.info(f"Action: Approving task '{refined_task.chapter_title}'...")
        return ApprovedTask(chapter_title=refined_task.chapter_title, refined_task=refined_task)

class ChiefPM(DocWriterBaseRole):
    name: str = "ChiefPM"
    profile: str = "Chief Product Manager"
    goal: str = "Oversee the entire document generation process and ensure final quality."
    revision_count: int = 0
    max_revisions: int = 3

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([DecomposeTopic(), ReviewAndCommand(llm_activation=self.llm_activation), ApproveTask()])
        self._watch({
            f"{UserRequirement.__module__}.{UserRequirement.__name__}",
            f"{FullDraft.__module__}.{FullDraft.__name__}",
            f"{QAReport.__module__}.{QAReport.__name__}",
            # FIX: 直接使用类型，更可靠
            RefinedTask,
        })
        self._set_react_mode(react_mode="react", max_react_loop=1)

    async def _think(self) -> None:
        # --- 添加日志点 C & D ---
        if not self.rc.news:
            logger.debug(f"ChiefPM _think: No new messages observed in this turn.")
            return

        observed_news = [f"'{type(msg.instruct_content).__name__}' from '{msg.role}'" for msg in self.rc.news]
        logger.info(f"ChiefPM _think: Observed {len(self.rc.news)} new messages: {observed_news}")

        if self.rc.todo:
            logger.debug(f"ChiefPM _think: Already has a todo: {self.rc.todo.name}. Skipping further thinking.")
            return
        
        msg = self.rc.news[-1]
        self.rc.todo = None
        
        logger.debug(f"ChiefPM _think: Evaluating last message of type '{type(msg.instruct_content).__name__}' with cause_by '{msg.cause_by}'")

        if msg.cause_by == f"{UserRequirement.__module__}.{UserRequirement.__name__}":
            self.rc.todo = self.actions[0] # DecomposeTopic
            logger.info(f"ChiefPM _think: Matched UserRequirement. Setting todo to 'DecomposeTopic'.")
        elif isinstance(msg.instruct_content, RefinedTask):
            self.rc.todo = self.actions[2] # ApproveTask
            logger.success(f"ChiefPM _think: Matched RefinedTask! Setting todo to 'ApproveTask'.")
        elif isinstance(msg.instruct_content, FullDraft):
            if self.revision_count < self.max_revisions:
                self.rc.todo = self.actions[1] # ReviewAndCommand
                logger.info(f"ChiefPM _think: Matched FullDraft. Setting todo to 'ReviewAndCommand'.")
        
        if self.rc.todo:
             logger.info(f"{self.name} is planning to {self.rc.todo.name}.")
        else:
            logger.warning(f"ChiefPM _think: After evaluating all new messages, no action was planned.")

    async def _act(self) -> Message:
        if self.revision_count >= self.max_revisions and isinstance(self.rc.history[-1].instruct_content, FullDraft):
            logger.warning(f"Max revisions ({self.max_revisions}) reached. Forcing approval.")
            approval_msg = Approval(comment=f"Approved after reaching max {self.max_revisions} revisions.")
            return Message(instruct_content=approval_msg, role=self.profile, cause_by=self.__class__)

        if not self.rc.todo: return None
        
        action = self.rc.todo
        logger.info(f"{self.name}: ready to {action.name}")
        msg = self.rc.history[-1]
        
        run_kwargs = {}
        original_topic = ""
        
        if isinstance(action, DecomposeTopic):
            original_topic = msg.content
            run_kwargs['topic'] = original_topic
            run_kwargs['use_llm'] = self.llm_activation.get(action.name, False)
        elif isinstance(action, ReviewAndCommand):
            self.revision_count += 1
            logger.info(f"Revision attempt {self.revision_count}/{self.max_revisions}.")
            run_kwargs['full_draft'] = self.rc.memory.get_by_class(FullDraft)[-1].instruct_content
            qa_report_list = self.rc.memory.get_by_class(QAReport)
            if qa_report_list:
                run_kwargs['qa_report'] = qa_report_list[-1].instruct_content
        elif isinstance(action, ApproveTask):
            run_kwargs['refined_task'] = msg.instruct_content
            
        response_obj = await action.run(**run_kwargs)
        
        if isinstance(response_obj, ReviewNotes) and ("no changes" in response_obj.feedback.lower() or "looks good" in response_obj.feedback.lower()):
            logger.info("Review resulted in no changes. Approving document.")
            return Message(instruct_content=Approval(comment="Approved based on review."))

        content_for_downstream = original_topic or response_obj.model_dump_json(indent=2)
        return Message(content=content_for_downstream, instruct_content=response_obj, role=self.profile, cause_by=type(action))