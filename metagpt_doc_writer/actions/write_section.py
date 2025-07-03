
from metagpt.actions import Action
from metagpt_doc_writer.schemas.doc_structures import ApprovedTask, DraftSection
from metagpt.schema import Message
from metagpt.utils.common import OutputParser
from metagpt_doc_writer.prompts.self_reflection_prompt import SELF_REFLECTION_PROMPT_TEMPLATE
import json

class WriteSection(Action):
    async def run(self, task: ApprovedTask) -> DraftSection:
        # Generate initial draft
        initial_prompt = f"""
        You are a technical writer. Write a draft section based on the following approved task:

        Title: {task.chapter_title}
        Context: {task.refined_task.context}
        Goals: {', '.join(task.refined_task.goals)}
        Acceptance Criteria: {', '.join(task.refined_task.acceptance_criteria)}

        Your draft should be comprehensive and directly address all goals and acceptance criteria.
        """
        initial_draft_rsp = await self._aask(initial_prompt)
        initial_draft_content = initial_draft_rsp.content

        # Self-reflection and refinement
        refined_draft_content = await self._reflect(initial_draft_content, task)

        return DraftSection(
            chapter_id=task.chapter_title, # Using title as ID for simplicity
            content=refined_draft_content
        )

    async def _reflect(self, draft_content: str, task: ApprovedTask) -> str:
        request_str = f"""
        Title: {task.chapter_title}
        Context: {task.refined_task.context}
        Goals: {', '.join(task.refined_task.goals)}
        Acceptance Criteria: {', '.join(task.refined_task.acceptance_criteria)}
        """
        reflection_prompt = SELF_REFLECTION_PROMPT_TEMPLATE.safe_substitute(request=request_str, output=draft_content)
        
        reflection_rsp = await self._aask(reflection_prompt)
        
        try:
            reflection_data = OutputParser.extract_struct(reflection_rsp.content, dict)
            # Calculate total score
            completeness = reflection_data.get('Evaluate', {}).get('Completeness', 0)
            clarity = reflection_data.get('Evaluate', {}).get('Clarity', 0)
            accuracy = reflection_data.get('Evaluate', {}).get('Accuracy', 0)
            total_score = completeness + clarity + accuracy

            if total_score < 13 and reflection_data.get('Revise'):
                return reflection_data['Revise']
            else:
                return draft_content
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing reflection JSON: {e}")
            return draft_content # Return original content if parsing fails

