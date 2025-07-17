# /root/metagpt/mgfr/metagpt_doc_writer/actions/review.py

from metagpt.actions import Action
from metagpt.logs import logger
from typing import ClassVar

class Review(Action):

    PROMPT_TEMPLATE: ClassVar[str] = """
    You are a meticulous editor. Please review the following content based on the instruction.
    Instruction: "{instruction}"
    --- CONTENT TO REVIEW ---
    {context}
    --- END OF CONTENT ---
    Provide your review comments, or if the instruction is to revise, provide the revised content directly. Your output should be the review result itself.
    """
    
    async def run(self, instruction: str, context: str = "", **kwargs) -> str:
        logger.info(f"Executing Review Action with instruction: {instruction}")
        prompt = self.PROMPT_TEMPLATE.format(instruction=instruction, context=context)
        result = await self._aask(prompt, system_msgs=["You are a meticulous editor."])
        return result