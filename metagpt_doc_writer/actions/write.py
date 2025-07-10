# 路径: /root/metagpt/mgfr/metagpt_doc_writer/actions/write.py (最终实现版)

from metagpt.actions import Action
from metagpt.logs import logger
from typing import ClassVar

class Write(Action):
    PROMPT_TEMPLATE: ClassVar[str] = """
    Your task is to write a piece of content based on the provided instruction.
    
    Instruction: "{instruction}"
    
    Here is the context from previous steps, which you should use to inform your writing:
    --- CONTEXT START ---
    {context}
    --- CONTEXT END ---
    
    Please provide the complete, well-structured content now. Only output the content, without any extra commentary.
    """
    
    def __init__(self, name="WRITE", **kwargs):
        super().__init__(name=name, **kwargs)
        
    async def run(self, instruction: str, context: str = "", *args, **kwargs) -> str:
        logger.info(f"Executing Write Action with instruction: {instruction}")

        prompt = self.PROMPT_TEMPLATE.format(instruction=instruction, context=context)
        
        # [实现] 调用LLM来执行真正的写作
        result = await self.llm.aask(prompt, system_msgs=["You are a professional technical writer."])
        
        logger.info(f"Writing result for '{instruction}':\n{result[:200]}...")
        return result