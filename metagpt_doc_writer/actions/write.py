# /root/metagpt/mgfr/metagpt_doc_writer/actions/write.py

from metagpt.actions import Action
from metagpt.logs import logger
from typing import ClassVar

class Write(Action):
    PROMPT_TEMPLATE: ClassVar[str] = "Placeholder for writing prompt: {instruction} with context {context}"
    
    def __init__(self, name="WRITE", **kwargs):
        super().__init__(name=name, **kwargs)
        
    async def run(self, instruction: str, context: str = "", *args, **kwargs) -> str:
        logger.info(f"Executing Mock Write for: {instruction}")
        return f"Mocked written content for instruction: '{instruction}' based on provided context."