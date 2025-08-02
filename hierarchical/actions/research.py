# mghier/hierarchical/actions/research.py (阶段二: ReAct循环与任务记忆)

import sys
import json
import uuid
import shutil
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# -----------------

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.utils.common import CodeParser
from metagpt.schema import Message
from metagpt.memory.role_zero_memory import RoleZeroLongTermMemory

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

# ReAct循环中使用的Prompt模板
REACT_PROMPT = """
You are an expert research assistant using a ReAct (Reasoning + Action) framework. Based on the original goal and the information gathered so far, decide on the next best action.

**Original Goal:**
"{original_goal}"

**Available Tools:**
{available_tools}

**Important Notes for Tool Usage:**
- When using the 'resolve-library-id' tool, you MUST provide the 'libraryName' argument (not 'query').
- When using the 'get-library-docs' tool, you MUST provide the 'context7CompatibleLibraryID' argument (not 'library_id').

**Information Gathered So Far (Scratchpad):**
{scratchpad}

Based on the information above, think about what to do next and then decide on an action. Respond with a single, valid JSON object. Choose one of the following formats:

1.  To use a tool:
    ```json
    {{
      "thought": "<Your reasoning about what to do next>",
      "action": {{
        "tool_name": "<tool_name>",
        "tool_args": {{...}}
      }}
    }}
    ```

2.  To finish the task:
    ```json
    {{
      "thought": "<Your final reasoning>",
      "action": {{
        "tool_name": "FINISH",
        "result": "<The final result of your research>"
      }}
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
        # 确保llm属性被正确设置
        if llm is None and not hasattr(self, 'llm'):
            # 如果既没有提供llm，父类也没有设置llm，则设置为None
            # 这样会使用Action类的默认行为
            self.llm = None

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

    def _parse_thought_action(self, decision_str: str) -> tuple[str, dict]:
        """解析LLM的决策字符串，提取thought和action。使用多种策略处理不同的LLM输出格式。"""
        
        # Strategy 1: Try CodeParser first (handles markdown-wrapped JSON)
        try:
            decision_json_str = CodeParser.parse_code(text=decision_str)
            if decision_json_str != decision_str:  # CodeParser found and extracted JSON
                decision = json.loads(decision_json_str)
                thought = decision.get("thought", "")
                action = decision.get("action", {})
                return thought, action
        except Exception as e:
            logger.debug(f"CodeParser failed: {e}, trying alternative parsing methods")
        
        # Strategy 2: Try to find and extract JSON object from mixed text
        json_match = self._extract_json_from_mixed_text(decision_str)
        if json_match:
            try:
                decision = json.loads(json_match)
                
                # Case 1: JSON contains both thought and action (standard format)
                if "thought" in decision and "action" in decision:
                    thought = decision.get("thought", "")
                    action = decision.get("action", {})
                    return thought, action
                
                # Case 2: JSON contains only action (mixed text format)
                elif "tool_name" in decision or "action" in decision:
                    thought = self._extract_thought_from_text(decision_str, json_match)
                    # If the JSON has an "action" key, use it; otherwise assume the JSON itself is the action
                    if "action" in decision:
                        action = decision.get("action", {})
                    else:
                        action = decision
                    return thought, action
                
                # Case 3: JSON contains only thought (unusual but possible)
                elif "thought" in decision:
                    thought = decision.get("thought", "")
                    action = {}
                    return thought, action
                    
            except json.JSONDecodeError as e:
                logger.debug(f"Extracted JSON parsing failed: {e}")
        
        # Strategy 3: Try to parse Action JSON from common patterns
        action_match = self._extract_action_from_patterns(decision_str)
        if action_match:
            try:
                action = json.loads(action_match)
                # Extract thought from surrounding text
                thought = self._extract_thought_from_text(decision_str, action_match)
                return thought, action
            except json.JSONDecodeError as e:
                logger.debug(f"Action pattern parsing failed: {e}")
        
        # Strategy 4: Parse manually by splitting text and looking for Action section
        thought, action = self._manual_parse_text_format(decision_str)
        if action:
            return thought, action
        
        # Strategy 5: Last resort - try to parse entire string as JSON
        try:
            decision = json.loads(decision_str.strip())
            thought = decision.get("thought", "")
            action = decision.get("action", {})
            return thought, action
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"All JSON parsing strategies failed: {e}")
            logger.error(f"Decision string: {decision_str}")
            raise

    def _extract_json_from_mixed_text(self, text: str) -> Optional[str]:
        """从混合文本中提取JSON对象。使用简单的平衡括号匹配方法。"""
        
        def find_json_object(s: str, start_pos: int = 0) -> Optional[str]:
            """从指定位置开始查找JSON对象。"""
            brace_count = 0
            start_idx = -1
            
            for i in range(start_pos, len(s)):
                char = s[i]
                if char == '{':
                    if brace_count == 0:
                        start_idx = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and start_idx != -1:
                        # Found a complete JSON object
                        json_str = s[start_idx:i+1]
                        try:
                            json.loads(json_str)  # Validate it's valid JSON
                            return json_str
                        except json.JSONDecodeError:
                            continue
            
            return None
        
        # Try to find JSON objects throughout the text
        for i in range(len(text)):
            if text[i] == '{':
                json_match = find_json_object(text, i)
                if json_match:
                    return json_match
        
        # If no balanced JSON found, try pattern-based extraction as fallback
        # Look for objects with "thought" and "action" keys
        thought_action_pattern = r'\{[^}]*"thought"[^}]*"action"[^}]*\}'
        match = re.search(thought_action_pattern, text, re.DOTALL)
        if match:
            try:
                json.loads(match.group(0))
                return match.group(0)
            except json.JSONDecodeError:
                pass
        
        # Look for objects with "tool_name" key
        tool_pattern = r'\{[^}]*"tool_name"[^}]*\}'
        match = re.search(tool_pattern, text, re.DOTALL)
        if match:
            try:
                json.loads(match.group(0))
                return match.group(0)
            except json.JSONDecodeError:
                pass
        
        return None

    def _extract_action_from_patterns(self, text: str) -> Optional[str]:
        """从常见模式中提取Action JSON。"""
        # Pattern 1: Look for "Action: { ... }" pattern
        action_pattern = r'Action:\s*(\{[^}]*\})'
        match = re.search(action_pattern, text, re.DOTALL)
        if match:
            return match.group(1)
        
        # Pattern 2: Look for action-like JSON with tool_name
        tool_pattern = r'\{[^}]*"tool_name"[^}]*\}'
        match = re.search(tool_pattern, text, re.DOTALL)
        if match:
            return match.group(1)
        
        # Pattern 3: Look for FINISH action
        finish_pattern = r'\{[^}]*"tool_name"\s*:\s*"FINISH"[^}]*\}'
        match = re.search(finish_pattern, text, re.DOTALL)
        if match:
            return match.group(1)
        
        return None

    def _extract_thought_from_text(self, text: str, json_part: str) -> str:
        """从文本中提取thought，排除JSON部分。"""
        # Remove the JSON part from the text
        text_without_json = text.replace(json_part, '').strip()
        
        # Look for thought patterns
        thought_patterns = [
            r'Thought:\s*(.*?)(?=\nAction:|\n\n|$)',
            r'(?:Step\s*\d+:\s*)?Thought:\s*(.*?)(?=\nAction:|\n\n|$)',
            r'(?:Step\s*\d+:\s*)?(.*?)(?=\nAction:)'
        ]
        
        for pattern in thought_patterns:
            match = re.search(pattern, text_without_json, re.DOTALL | re.IGNORECASE)
            if match:
                thought = match.group(1).strip()
                # Remove "Step X: Thought:" prefix if present
                thought = re.sub(r'^Step\s*\d+:\s*Thought:\s*', '', thought, flags=re.IGNORECASE)
                return thought
        
        # Fallback: return the text before the Action section
        lines = text_without_json.split('\n')
        thought_lines = []
        for line in lines:
            line = line.strip()
            if line.lower().startswith('action:'):
                break
            if line and not line.lower().startswith('step'):
                thought_lines.append(line)
        
        return ' '.join(thought_lines).strip()

    def _manual_parse_text_format(self, text: str) -> Tuple[str, dict]:
        """手动解析文本格式，提取thought和action。"""
        lines = text.split('\n')
        thought = ""
        action_str = ""
        found_action = False
        
        # First pass: Extract thought
        for line in lines:
            line = line.strip()
            if line.lower().startswith('thought:'):
                thought = line[len('Thought:'):].strip()
                break
            elif line.lower().startswith('step') and 'thought:' in line.lower():
                # Handle "Step X: Thought: ..." format
                parts = line.split('Thought:', 1)
                if len(parts) > 1:
                    thought = parts[1].strip()
                    break
        
        # Second pass: Extract action
        action_line_patterns = [
            r'^Action:\s*(\{.*\})$',
            r'^.*Action:\s*(\{.*\})$',
            r'^(\{.*"tool_name".*\})$'
        ]
        
        for line in lines:
            line = line.strip()
            for pattern in action_line_patterns:
                match = re.match(pattern, line, re.DOTALL)
                if match:
                    action_str = match.group(1)
                    found_action = True
                    break
            if found_action:
                break
        
        # If no action found in single line, look for multi-line JSON
        if not action_str:
            # Look for Action: followed by JSON on next lines
            action_start = -1
            for i, line in enumerate(lines):
                if line.strip().lower().startswith('action:'):
                    action_start = i + 1
                    break
            
            if action_start >= 0 and action_start < len(lines):
                # Collect all subsequent lines that look like JSON
                json_lines = []
                for i in range(action_start, len(lines)):
                    line = lines[i].strip()
                    if line and (line.startswith('{') or '}' in line or line.startswith('"') or line.startswith(' ')):
                        json_lines.append(line)
                    elif json_lines:  # Stop if we hit a non-JSON line after starting JSON
                        break
                
                if json_lines:
                    action_str = ''.join(json_lines)
        
        # Try to parse action_str as JSON
        if action_str:
            try:
                action = json.loads(action_str)
                return thought, action
            except json.JSONDecodeError:
                pass
        
        # Final fallback: Try to find any JSON object in the text
        json_match = self._extract_json_from_mixed_text(text)
        if json_match:
            try:
                action = json.loads(json_match)
                # If thought is empty, extract it from text
                if not thought:
                    thought = self._extract_thought_from_text(text, json_match)
                return thought, action
            except json.JSONDecodeError:
                pass
        
        return "", {}

    async def _execute_tool(self, action: dict) -> str:
        """执行工具调用并返回观察结果。"""
        tool_name = action.get("tool_name")
        tool_args = action.get("tool_args", {})
        
        if tool_name == "FINISH":
            return action.get("result", "Task completed.")
        
        logger.info(f"Executing tool '{tool_name}' with args: {tool_args}")
        try:
            # 直接调用MCP工具，不需要前缀
            if hasattr(self.context, 'mcp_manager'):
                result_str = await self.context.mcp_manager.call_tool(tool_name, tool_args)
                return result_str
            else:
                return f"No MCP manager available for tool: {tool_name}"
        except Exception as e:
            logger.error(f"Tool '{tool_name}' execution failed: {e}", exc_info=True)
            return f"Error executing tool '{tool_name}': {str(e)}"

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
            logger.info(f"Processing query with ReAct cycle: '{query}'")
            
            # 生成唯一的任务ID
            task_id = f"research_task_{uuid.uuid4().hex}"
            temp_memory_path = f"./.tmp_task_memories/{task_id}"
            task_memory = None
            
            try:
                # 动态实例化一个任务级别的记忆系统
                task_memory = RoleZeroLongTermMemory(
                    persist_path=temp_memory_path,
                    collection_name=task_id,
                    memory_k=5  # 使用较低的memory_k，因为我们希望观察结果尽快进入RAG
                )
                
                # 构建工具描述信息
                tools_info = {}
                if tool_descriptions:
                    # 解析工具描述，构建工具映射
                    tools_info = self._parse_tool_descriptions(tool_descriptions)
                
                # 开始ReAct循环
                max_react_loops = kwargs.get('max_react_loops', 10)
                final_result = await self._run_react_cycle(
                    query, task_memory, tools_info, max_react_loops
                )
                
                final_results[query] = final_result
                
            except Exception as e:
                logger.error(f"ReAct cycle failed for query '{query}': {e}", exc_info=True)
                final_results[query] = {
                    "status": "failure",
                    "source": "react_cycle",
                    "final_answer": "ReAct research failed.",
                    "reason": str(e)
                }
                
            finally:
                # 确保在任务结束时清理临时记忆文件
                if temp_memory_path and Path(temp_memory_path).exists():
                    shutil.rmtree(temp_memory_path)
                    logger.info(f"Cleaned up temporary task memory at {temp_memory_path}")
        
        return final_results

    def _parse_tool_descriptions(self, tool_descriptions: str) -> Dict[str, str]:
        """解析工具描述字符串，构建工具映射。"""
        # 这里可以根据实际的工具描述格式进行解析
        # 暂时返回一个简单的映射
        tools = {}
        lines = tool_descriptions.strip().split('\n')
        for line in lines:
            if line.strip():
                # 简单的解析逻辑，假设每行包含工具名称和描述
                if ':' in line:
                    name, desc = line.split(':', 1)
                    tools[name.strip()] = desc.strip()
        return tools

    async def _run_react_cycle(self, query: str, task_memory: RoleZeroLongTermMemory, 
                              tools_info: Dict[str, str], max_loops: int) -> Dict[str, Any]:
        """执行ReAct循环的核心逻辑。"""
        logger.info(f"Starting ReAct cycle for query: '{query}'")
        
        for i in range(max_loops):
            try:
                # 1. 从TaskMemory获取动态上下文/历史
                history_messages = task_memory.get()
                scratchpad = "\n".join([
                    f"Step {j+1}: {msg.content}" for j, msg in enumerate(history_messages)
                ])
                
                # 2. 构建思考的Prompt
                prompt = REACT_PROMPT.format(
                    original_goal=query,
                    available_tools="\n".join([f"{name}: {desc}" for name, desc in tools_info.items()]),
                    scratchpad=scratchpad
                )
                
                # 3. LLM 思考并决定下一步行动
                decision_str = await self._aask(prompt)
                thought, action = self._parse_thought_action(decision_str)
                
                # 4. 执行行动并获取观察结果
                observation = await self._execute_tool(action)
                
                # 5. 将观察结果存入TaskMemory
                observation_msg = Message(
                    content=f"Thought: {thought}\nAction: {json.dumps(action)}\nObservation: {observation}"
                )
                task_memory.add(observation_msg)
                
                # 6. 检查是否结束
                if action.get("tool_name") == "FINISH":
                    logger.info(f"ReAct cycle completed after {i+1} steps")
                    return {
                        "status": "success",
                        "source": "react_cycle",
                        "final_answer": observation,
                        "steps_taken": i + 1
                    }
                
            except Exception as e:
                logger.error(f"ReAct step {i+1} failed: {e}", exc_info=True)
                # 将错误信息存入记忆中，以便LLM在下一步可以处理
                error_msg = Message(
                    content=f"Step {i+1} failed with error: {str(e)}"
                )
                task_memory.add(error_msg)
        
        # 达到最大循环次数仍未完成
        return {
            "status": "failure",
            "source": "react_cycle",
            "final_answer": "ReAct cycle reached maximum iterations without completion.",
            "steps_taken": max_loops
        }