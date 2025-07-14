# /root/metagpt/mgfr/metagpt_doc_writer/actions/decompose_topic.py (已修正)

from typing import List
from metagpt.actions import Action
from metagpt.actions.action_node import ActionNode
from metagpt.logs import logger
# --- 修正: 使用绝对路径导入 ---
from mgfr.metagpt_doc_writer.schemas.doc_structures import ProjectPlan

DECOMPOSE_NODE = ActionNode(
    key="modules",
    expected_type=List[str],
    instruction="As an expert project manager, break down the user's requirement into a logical project plan. Generate 3-5 main module titles.",
    example=["1. Introduction", "2. Core Concepts", "3. Advanced Usage"]
)

class DecomposeTopic(Action):
    name: str = "DecomposeTopic"

    async def run(self, topic: str) -> ProjectPlan:
        logger.info(f"Action: Decomposing topic '{topic}' with ActionNode.fill()...")
        try:
            result_node = await DECOMPOSE_NODE.fill(
                req=f"User Requirement: '{topic}'",
                llm=self.llm,
                schema="json"
            )
            modules = result_node.instruct_content.modules
            logger.info(f"ActionNode.fill() successfully returned modules: {modules}")
            return ProjectPlan(modules=modules)
        except Exception as e:
            logger.error(f"ActionNode.fill() failed for DecomposeTopic. Error: {e}", exc_info=True)
            return ProjectPlan(modules=[f"Default Plan for '{topic}' due to ActionNode error."])