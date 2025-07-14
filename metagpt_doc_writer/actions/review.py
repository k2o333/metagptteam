# /root/metagpt/mgfr/metagpt_doc_writer/actions/review.py

from metagpt.actions import Action
from metagpt.logs import logger
from typing import ClassVar

class Review(Action):
    PROMPT_TEMPLATE: ClassVar[str] = "Placeholder for review prompt: {instruction} on content {context}"
    
    def __init__(self, name="REVIEW", **kwargs):
        super().__init__(name=name, **kwargs)

    async def run(self, instruction: str, context: str = "", *args, **kwargs) -> str:
        logger.info(f"Executing Mock Review for: {instruction}")
        return f"Mocked review comments for instruction: '{instruction}'."