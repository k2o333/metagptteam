# 路径: /root/metagpt/mgfr/metagpt_doc_writer/actions/research.py (最终实现版)

from metagpt.actions import Action
from metagpt.logs import logger
from typing import ClassVar

class Research(Action):
    PROMPT_TEMPLATE: ClassVar[str] = """
    Please research the following topic based on the user's instruction.
    Your goal is to provide a concise and informative summary that will be used as context for later tasks.
    
    Instruction: "{instruction}"
    
    Provide a detailed summary of your findings.
    """
    
    def __init__(self, name="RESEARCH", **kwargs):
        super().__init__(name=name, **kwargs)

    async def run(self, instruction: str, *args, **kwargs) -> str:
        logger.info(f"Executing Research Action with instruction: {instruction}")
        
        prompt = self.PROMPT_TEMPLATE.format(instruction=instruction)
        
        # [实现] 调用LLM来执行真正的研究
        result = await self.llm.aask(prompt, system_msgs=["You are a professional researcher."])
        
        logger.info(f"Research result for '{instruction}':\n{result[:200]}...")
        return result