# mghier/hierarchical/actions/revise_section.py (修复版)

from metagpt.actions import Action
from metagpt.logs import logger

class ReviseSection(Action):
    name: str = "ReviseSection"
    
    # 【核心修复】在 run 方法签名中添加 **kwargs
    async def run(self, context: dict, review_comments: str, **kwargs) -> str:
        """
        Simulates revising a section based on review comments.
        It now accepts **kwargs to ignore any extra parameters.
        """
        logger.info(f"Simulating revision for section: {context.get('target_section_title')} based on comments: {review_comments}")
        # 实际场景中，这里会调用LLM
        return context.get("original_content", "") + "\n\n--- Revised ---"