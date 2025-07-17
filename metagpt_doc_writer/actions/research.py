# /root/metagpt/mgfr/metagpt_doc_writer/actions/research.py

from metagpt.actions import Action
from metagpt.logs import logger
from typing import ClassVar

# 【核心修正】: 不再导入SearchEngine，因为我们不再直接使用它
# from metagpt.tools.search_engine import SearchEngine

class Research(Action):
    """
    一个专门用于执行研究任务的Action。
    为了规避底层依赖库的稳定性问题，本版本的网络搜索功能已被一个
    返回固定提示信息的模拟逻辑所取代。
    """
    # 移除显式定义的name属性，让框架使用类名"Research"作为默认name
    
    PROMPT_TEMPLATE: ClassVar[str] = """
    You are a professional researcher and analyst. Your task is to provide a comprehensive summary based on the user's instruction and any provided context.

    **User Instruction**: 
    "{instruction}"
    
    **Context from external sources (if any)**:
    ---
    {search_context}
    ---
    
    Please synthesize all available information and provide a detailed, well-structured summary of your findings now, relying primarily on your internal knowledge.
    """

    async def run(self, instruction: str, context: str = "", **kwargs) -> str:
        """
        执行研究任务。
        """
        logger.info(f"Executing Research Action for: '{instruction}'")

        # 【核心修正】: 彻底移除对SearchEngine的调用，用一个稳定的模拟逻辑替代
        logger.warning(
            "Due to a persistent underlying bug in the search dependency, "
            "the web search functionality is currently disabled in this action. "
            "The process will continue based on the LLM's internal knowledge."
        )
        search_context_str = (
            "Note: Web search functionality is currently unavailable. "
            "The following analysis is based on the language model's pre-existing knowledge."
        )
        
        # 将上游任务的context（如果有的话）和我们的固定笔记结合
        full_context = f"{context}\n\n{search_context_str}".strip()
        
        prompt = self.PROMPT_TEMPLATE.format(
            instruction=instruction, 
            search_context=full_context
        )
        
        # self.llm 已经由框架通过context正确注入
        result = await self._aask(prompt)
        
        logger.info(f"Research result for '{instruction}' generated.")
        return result