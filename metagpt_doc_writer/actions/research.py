# /root/metagpt/mgfr/metagpt_doc_writer/actions/research.py (最终修正版 V2)

from metagpt.actions import Action
from metagpt.logs import logger
from typing import ClassVar, Optional
from metagpt_doc_writer.mcp.manager import MCPManager

class Research(Action):
    PROMPT_TEMPLATE: ClassVar[str] = """
    Please perform a comprehensive research based on the user's instruction and the provided context from a web search.
    Your goal is to synthesize the information into a concise and informative summary that will be used for subsequent writing tasks.
    
    User Instruction: "{instruction}"
    
    {search_context}
    
    Provide a detailed summary of your findings now.
    """
    
    def __init__(self, name="RESEARCH", **kwargs):
        super().__init__(name=name, **kwargs)

    # 【核心修正】: run方法签名改变，显式接收所需依赖，不再使用self.owner
    async def run(
        self, 
        instruction: str, 
        context: str = "",
        mcp_manager: Optional[MCPManager] = None, # 接收manager
        can_use_tool: bool = False # 直接接收权限检查的结果
    ) -> str:
        logger.info(f"Executing Research Action for: '{instruction}'")

        search_context_str = ""
        
        if mcp_manager and can_use_tool:
            logger.info("Web search tool is available for this role. Performing search...")
            try:
                search_result = await mcp_manager.call_tool(
                    tool_name="web_search", 
                    args={"query": instruction}
                )
                search_context_str = f"### Context from Web Search:\n{search_result}"
                logger.success("Web search completed successfully.")
            except Exception as e:
                logger.error(f"An error occurred during web search: {e}", exc_info=True)
                search_context_str = "### Note: Web search failed during execution."
        else:
            logger.info("Web search tool not available or not permitted for this role.")

        full_context = f"{context}\n\n{search_context_str}".strip()
        prompt = self.PROMPT_TEMPLATE.format(instruction=instruction, search_context=full_context)
        
        result = await self.llm.aask(prompt, system_msgs=["You are a professional researcher and analyst."])
        
        logger.info(f"Research result for '{instruction}' generated.")
        return result