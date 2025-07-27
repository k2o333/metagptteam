# mghier/hierarchical/actions/research.py (阶段一最终集成版)

import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# -----------------

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.utils.common import CodeParser

from hierarchical.rag.engines.docrag_engine import DocRAGEngine 
from hierarchical.schemas import RAGResponse

# 为LLM决策设计的Prompt模板
DECISION_PROMPT_TEMPLATE = """
You are an expert research assistant. Your task is to decide the best way to answer the user's query.

**User Query:**
"{query}"

You have the following options:
1.  **Use an external tool**: If the query seems to require up-to-date, specific, or API-like information (e.g., finding a library ID, fetching documentation), you can use a tool.
2.  **Use internal knowledge base**: If the query is more general or conceptual, you can search the internal knowledge base (DocRAG).
3.  **Answer directly**: If the query is very simple and you know the answer, you can answer it directly.

**Available Tools:**
{tool_descriptions}

**Your Decision:**
Respond with a single, valid JSON object. Choose one of the following formats:

1.  To use a tool:
    ```json
    {{
      "decision": "use_tool",
      "tool_call": {{
        "name": "<tool_name>",
        "arguments": {{...}}
      }}
    }}
    ```
    Example: {{"decision": "use_tool", "tool_call": {{"name": "resolve-library-id", "arguments": {{"libraryName": "react"}}}}}}

2.  To use the internal knowledge base:
    ```json
    {{
      "decision": "use_internal_rag"
    }}
    ```

3.  To answer directly:
    ```json
    {{
      "decision": "direct_answer",
      "answer": "<Your direct answer here>"
    }}
    ```

Provide ONLY the JSON object in your response.
"""

# 用于总结的Prompt模板
SYNTHESIS_PROMPT_TEMPLATE = """
You are a research analyst. Your task is to provide a concise and helpful answer to the user's original query based on the information you have gathered.

**Original Query:**
"{query}"

**Gathered Information / Context:**
---
{context_data}
---

Based *only* on the information provided above, please synthesize a final answer to the original query.
If the gathered information is irrelevant or insufficient to answer the query, please state that clearly.
"""

class Research(Action):
    
    def __init__(self, name: str = "", context: Any = None, llm: Any = None):
        super().__init__(name=name, context=context, llm=llm)
        self.rag_engine: DocRAGEngine | None = None

    def set_docrag_engine(self, engine: DocRAGEngine | None):
        """
        一个方法，用于从外部（Role）注入RAG引擎实例。
        """
        self.rag_engine = engine
        if engine:
            logger.info("DocRAGEngine has been set for the Research action.")
        else:
            logger.warning("A null DocRAGEngine was set for the Research action. Internal search will be disabled.")


    async def _call_mcp_tool(self, tool_call: dict) -> dict:
        """Helper function to call an MCP tool."""
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("arguments", {})
        logger.info(f"Executing MCP tool '{tool_name}' with args: {tool_args}")
        try:
            result_str = await self.context.mcp_manager.call_tool(tool_name, tool_args)
            result_content = json.loads(result_str)
            return {
                "status": "success",
                "source": f"mcp_tool:{tool_name}",
                "raw_data": result_content
            }
        except Exception as e:
            logger.error(f"MCP tool '{tool_name}' call failed: {e}", exc_info=True)
            return { "status": "failure", "source": f"mcp_tool:{tool_name}", "reason": str(e) }

    async def _search_internal_rag(self, query: str) -> dict:
        """Helper function to search the internal RAG."""
        logger.info(f"Searching internal DocRAG for query: '{query}'")
        
        if not self.rag_engine:
            logger.warning("Internal DocRAGEngine not available for this search.")
            return {"status": "failure", "source": "internal_docrag", "reason": "Engine not initialized"}
            
        retrieved_nodes = await self.rag_engine.asearch(query, top_k=3)
        retrieved_content = [node.get_content() for node in retrieved_nodes]
        
        return {
            "status": "success",
            "source": "internal_docrag",
            "raw_data": { "retrieved_data": retrieved_content }
        }

    async def _synthesize_answer(self, query: str, context_data: Any) -> str:
        """使用LLM将收集到的上下文数据总结成最终答案。"""
        logger.info("Synthesizing final answer from gathered information.")
        
        context_str = json.dumps(context_data, indent=2, ensure_ascii=False)
        prompt = SYNTHESIS_PROMPT_TEMPLATE.format(query=query, context_data=context_str)
        
        final_answer = await self._aask(prompt)
        return final_answer.strip()

    async def run(self, queries: List[str], tool_descriptions: str = "", **kwargs) -> Dict[str, Any]:
        final_results = {}
        for query in queries:
            logger.info(f"Processing query: '{query}'")
            
            gathered_info = None

            # 默认使用内部RAG，除非有外部工具
            if not tool_descriptions:
                logger.info("No tool descriptions provided. Defaulting to local DocRAGE.")
                gathered_info = await self._search_internal_rag(query)
            else:
                prompt = DECISION_PROMPT_TEMPLATE.format(query=query, tool_descriptions=tool_descriptions)
                response_str = await self._aask(prompt)
                
                try:
                    decision_json_str = CodeParser.parse_code(text=response_str, lang="json")
                    decision = json.loads(decision_json_str)
                    logger.debug(f"LLM decision for query '{query}': {decision}")
                    decision_type = decision.get("decision")

                    if decision_type == "use_tool":
                        gathered_info = await self._call_mcp_tool(decision.get("tool_call", {}))
                    elif decision_type == "use_internal_rag":
                        gathered_info = await self._search_internal_rag(query)
                    elif decision_type == "direct_answer":
                        final_results[query] = {
                            "status": "success",
                            "source": "llm_direct_answer",
                            "final_answer": decision.get("answer", "")
                        }
                        continue # 直接进入下一个query的处理
                    else: 
                        raise ValueError(f"Unknown decision type: {decision_type}")
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    logger.warning(f"Failed to parse LLM decision. Defaulting to internal RAG. Error: {e}")
                    gathered_info = await self._search_internal_rag(query)
            
            if gathered_info and gathered_info.get("status") == "success":
                final_answer = await self._synthesize_answer(query, gathered_info.get("raw_data"))
                final_results[query] = {
                    "status": "success", 
                    "source": gathered_info.get("source"),
                    "final_answer": final_answer, 
                    "raw_data": gathered_info.get("raw_data")
                }
            else:
                final_results[query] = {
                    "status": "failure", 
                    "source": gathered_info.get("source", "unknown"),
                    "final_answer": "Failed to gather information to answer the query.",
                    "reason": gathered_info.get("reason", "Unknown error")
                }
        
        return final_results