# mghier/hierarchical/actions/review_section.py (修复版)

from metagpt.actions import Action
from metagpt.logs import logger

class ReviewSection(Action):
    name: str = "ReviewSection"
    
    # 【核心修复】在 run 方法签名中添加 **kwargs
    async def run(self, context: dict, **kwargs) -> str:
        """
        Simulates reviewing a section.
        It now accepts **kwargs to ignore any extra parameters.
        """
        logger.info(f"Simulating review for section: {context.get('target_section_title')}")
        # 实际场景中，这里会调用LLM
        return "APPROVED"