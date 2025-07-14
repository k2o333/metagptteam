# /root/metagpt/mgfr/metagpt_doc_writer/actions/research.py

from metagpt.actions import Action
from metagpt.logs import logger
from typing import ClassVar, Optional, Dict
# from metagpt.tools.search_engine import SearchEngine # 不再需要
from metagpt_doc_writer.mcp.manager import MCPManager

class Research(Action):
    PROMPT_TEMPLATE: ClassVar[str] = """
    Please perform a comprehensive research based on the user's instruction and the provided context.
    Your goal is to synthesize all available information into a concise and informative summary that will be used for subsequent writing tasks.
    
    User Instruction: "{instruction}"
    
    {context_from_dependencies}
    
    {mcp_context}

    Provide a detailed summary of your findings now.
    """
    
    def __init__(self, name="RESEARCH", **kwargs):
        super().__init__(name=name, **kwargs)

    async def run(
        self, 
        instruction: str, 
        context: str = "",
        mcp_manager: Optional[MCPManager] = None,
        mcp_permissions: Optional[Dict[str, bool]] = None,
        **kwargs
    ) -> str:
        logger.info(f"Executing Research Action for: '{instruction}'")

        # 【核心修改】: 完全移除Web搜索逻辑
        logger.warning("Web search functionality has been temporarily disabled to ensure system stability.")
        
        # --- 使用MCP工具 (如果被启用并有权限) ---
        mcp_context_str = ""
        if mcp_manager and mcp_permissions:
            # 示例：检查是否被授予了'resolve-library-id'的权限
            if mcp_permissions.get("resolve-library-id"):
                try:
                    logger.info("Permission for 'resolve-library-id' granted. Attempting to use MCP tool...")
                    # 尝试从指令中解析库名 (这是一个简化的例子)
                    lib_name = "autogen" # 在真实场景中，这里应该用正则或LLM从instruction中提取
                    
                    lib_id_result_str = await mcp_manager.call_tool("resolve-library-id", {"libraryName": lib_name})
                    
                    # 假设返回的是JSON字符串，需要解析
                    import json
                    lib_id_data = json.loads(lib_id_result_str)
                    lib_id = lib_id_data[0]['text'] # 假设格式是 [{"type":"text", "text":"/pypi/autogen"}]
                    
                    logger.info(f"Resolved library ID for '{lib_name}': {lib_id}")

                    if lib_id and mcp_permissions.get("get-library-docs"):
                        logger.info("Permission for 'get-library-docs' granted. Fetching docs...")
                        docs_result_str = await mcp_manager.call_tool("get-library-docs", {"libraryId": lib_id})
                        mcp_context_str = f"### Context from Context7 MCP:\n{docs_result_str}"
                        logger.success("Successfully fetched library docs via MCP.")

                except Exception as e:
                    logger.error(f"An error occurred during MCP tool call: {e}", exc_info=True)
                    mcp_context_str = "### Note: MCP tool call failed during execution."
        
        # --- 组合所有信息并调用LLM ---
        full_prompt = self.PROMPT_TEMPLATE.format(
            instruction=instruction,
            context_from_dependencies=context,
            mcp_context=mcp_context_str # search_context被移除
        )
        
        result = await self._aask(full_prompt, system_msgs=["You are a professional researcher and analyst."])
        
        logger.info(f"Research result for '{instruction}' generated.")
        return result