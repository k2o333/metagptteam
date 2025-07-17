# /root/metagpt/mgfr/metagpt_doc_writer/actions/revise.py (新增文件)

from metagpt.actions import Action
from metagpt.logs import logger
from typing import ClassVar

class Revise(Action):
    """
    接收原始的文档片段(artifact)和评审意见(context)，输出一个修订后的新版本。
    """
    PROMPT_TEMPLATE: ClassVar[str] = """
    You are an expert technical writer, tasked with revising a document snippet based on review feedback.

    **Original Snippet to Revise**:
    ---
    {artifact}
    ---

    **Review Feedback and Suggestions**:
    ---
    {context}
    ---

    Please now provide the complete, revised version of the snippet, incorporating all the feedback.
    Your output should be ONLY the revised text, with no extra commentary.
    """
    
    # name属性将由框架根据类名自动设置为 "Revise"

    async def run(self, instruction: str, context: str, artifact: str, **kwargs) -> str:
        logger.info(f"Executing Revise Action for instruction: '{instruction}'")
        
        prompt = self.PROMPT_TEMPLATE.format(
            artifact=artifact,
            context=context # 评审意见来自上游的context
        )
        
        revised_content = await self._aask(prompt)
        return revised_content