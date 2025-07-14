# /root/metagpt/mgfr/metagpt_doc_writer/actions/research.py

from metagpt.actions import Action
from metagpt.logs import logger
from typing import ClassVar

class Research(Action):
    # Prompt可以先留空
    PROMPT_TEMPLATE: ClassVar[str] = "Placeholder for research prompt: {instruction}"
    
    # 关键：name需要和Task中的action_type匹配
    def __init__(self, name="RESEARCH", **kwargs):
        super().__init__(name=name, **kwargs)

    async def run(self, instruction: str, context: str = "", *args, **kwargs) -> str:
        logger.info(f"Executing Mock Research for: {instruction}")
        # 返回一个模拟结果，表明它被调用了
        return f"Mocked research result for instruction: '{instruction}'"