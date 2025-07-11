# 路径: /root/metagpt/mgfr/metagpt_doc_writer/actions/write_section.py (健壮解析修复版)

import json
from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.utils.common import OutputParser
from metagpt_doc_writer.prompts.self_reflection_prompt import SELF_REFLECTION_PROMPT_TEMPLATE
from metagpt_doc_writer.schemas.doc_structures import DraftSection, ApprovedTask

class WriteSection(Action):
    """
    An action to write a document section based on an ApprovedTask,
    with an integrated self-reflection and revision loop.
    """
    async def run(self, approved_task: ApprovedTask) -> DraftSection:
        """
        Executes the two-step process of writing and then reflecting/revising.
        """
        logger.info(f"Writing initial draft for: {approved_task.chapter_title}")
        initial_draft_content = await self._write_initial_draft(approved_task)
        
        logger.info(f"Performing self-reflection for: {approved_task.chapter_title}")
        final_content = await self._self_reflect_and_revise(approved_task.refined_task.goals, initial_draft_content)

        return DraftSection(chapter_id=approved_task.chapter_title, content=final_content)

    async def _write_initial_draft(self, approved_task: ApprovedTask) -> str:
        """
        Generates the first version of the document section.
        """
        prompt = f"""
        You are a professional technical writer. Your task is to write a detailed section for a document.
        
        **Chapter Title**: {approved_task.chapter_title}
        **Context**: {approved_task.refined_task.context}
        **Goals**: {', '.join(approved_task.refined_task.goals)}
        **Acceptance Criteria**: {', '.join(approved_task.refined_task.acceptance_criteria)}
        
        Please write the full content for this section now. Ensure it is well-structured, clear, and comprehensive.
        """
        return await self._aask(prompt)

    async def _self_reflect_and_revise(self, request_goals: list, initial_draft: str) -> str:
        """
        Uses a separate prompt to make the LLM review its own work and revise it.
        FIX: Implemented robust parsing for the reflection output.
        """
        prompt = SELF_REFLECTION_PROMPT_TEMPLATE.substitute(
            request=json.dumps(request_goals), 
            output=initial_draft
        )
        
        reflection_str = await self._aask(prompt)
        
        try:
            # Step 1: First, try to parse it as a raw JSON string.
            reflection_obj = json.loads(reflection_str)
        except json.JSONDecodeError:
            # Step 2: If raw parsing fails, assume it's wrapped in markdown and use OutputParser.
            logger.warning("Raw JSON parsing failed, attempting to extract from markdown code block.")
            try:
                reflection_obj = OutputParser.parse_code(text=reflection_str, lang="json")
                if isinstance(reflection_obj, str):
                    reflection_obj = json.loads(reflection_obj)
            except Exception as e:
                logger.error(f"Failed to parse self-reflection output with all methods. Error: {e}. Output: {reflection_str}")
                return initial_draft # Fallback to original draft

        # Once we have a dict, process it.
        if isinstance(reflection_obj, dict) and reflection_obj.get("Revise") and reflection_obj.get("Revise").strip():
            logger.info("Self-reflection resulted in a revision.")
            return reflection_obj["Revise"]
        else:
            logger.info("Self-reflection concluded that the initial draft is sufficient or revision is empty.")
            return initial_draft