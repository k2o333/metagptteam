# mghier/hierarchical/actions/research_controller.py (主要逻辑和编排)

import json
import re
import uuid
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.utils.common import CodeParser
from metagpt.schema import Message
from metagpt.memory.role_zero_memory import RoleZeroLongTermMemory
from metagpt.exp_pool import exp_cache

from .research_model import (
    ResearchConfig, ResearchResult, ResearchStep, ParsingStrategy, 
    ToolExecutionStatus
)
from .research_service import ToolExecutionService, InternalRAGService


# 用于总结的Prompt模板
SYNTHESIS_PROMPT_TEMPLATE = """
You are a research analyst. Your task is to provide a concise and helpful answer to the user's original query based on the information you have gathered.

{completion_instruction}

**Original Query:**
"{query}"

**Gathered Information / Context:**
---
{context_data}
---

Based *only* on the information provided above, please synthesize a final answer to the original query.
If the gathered information is irrelevant or insufficient to answer the query, please state that clearly.
"""

# ReAct循环中使用的Prompt模板
REACT_PROMPT = """
{system_prompt}
{tool_instruction}

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


class ResearchController:
    """Research控制器，负责整体逻辑编排"""
    
    def __init__(self, config: ResearchConfig = None):
        self.config = config or ResearchConfig()
        self.tool_service = ToolExecutionService(self.config)
        self.rag_service = InternalRAGService()
    
    def set_rag_engine(self, rag_engine):
        """设置RAG引擎"""
        self.rag_service = InternalRAGService(rag_engine)
        logger.info("DocRAGEngine has been set for the Research controller.")
    
    def set_context(self, context):
        """设置上下文"""
        self.context = context
    
    async def execute_research(self, queries: List[str], tool_descriptions: str = "", **kwargs) -> Dict[str, Any]:
        """执行研究查询"""
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
                    memory_k=5
                )
                
                # 解析工具描述
                tools_info = self._parse_tool_descriptions(tool_descriptions)
                
                # 开始ReAct循环
                max_react_loops = kwargs.get('max_react_loops', self.config.max_react_loops)
                research_result = await self._run_react_cycle(
                    query, task_memory, tools_info, max_react_loops
                )
                
                final_results[query] = research_result.to_dict()
                
            except Exception as e:
                logger.error(f"ReAct cycle failed for query '{query}': {e}", exc_info=True)
                research_result = ResearchResult(
                    query=query,
                    status=ToolExecutionStatus.FAILURE,
                    source="react_cycle",
                    final_answer="ReAct research failed.",
                    reason=str(e)
                )
                final_results[query] = research_result.to_dict()
                
            finally:
                # 清理临时记忆文件
                if temp_memory_path and Path(temp_memory_path).exists():
                    shutil.rmtree(temp_memory_path)
                    logger.info(f"Cleaned up temporary task memory at {temp_memory_path}")
        
        return final_results
    
    async def _run_react_cycle(self, query: str, task_memory: RoleZeroLongTermMemory, 
                              tools_info: Dict[str, str], max_loops: int) -> ResearchResult:
        """执行ReAct循环的核心逻辑"""
        logger.info(f"Starting ReAct cycle for query: '{query}'")
        research_result = ResearchResult(
            query=query,
            status=ToolExecutionStatus.FAILURE,
            source="react_cycle",
            final_answer="",
            steps_taken=0
        )
        
        for i in range(max_loops):
            try:
                # 1. 从TaskMemory获取动态上下文/历史
                history_messages = task_memory.get()
                scratchpad = "\n".join([
                    f"Step {j+1}: {msg.content}" for j, msg in enumerate(history_messages)
                ])
                
                # 2. 构建提示词
                prompt = self._build_react_prompt(query, tools_info, scratchpad)
                
                # 3. LLM思考并决定下一步行动
                try:
                    decision_str = await self._ask_llm(prompt)
                    thought, action = self._parse_thought_action(decision_str)
                except (ConnectionError, Exception) as e:
                    # LLM不可用时的fallback机制
                    logger.error(f"LLM unavailable in ReAct cycle: {e}")
                    research_result.reason = "LLM unavailable"
                    research_result.final_answer = "Research failed due to LLM unavailability"
                    return research_result
                
                # 4. 执行行动并获取观察结果
                observation = await self._execute_tool_action(action, query)
                
                # 5. 将观察结果存入TaskMemory
                observation_msg = Message(
                    content=f"Thought: {thought}\nAction: {json.dumps(action)}\nObservation: {observation}"
                )
                task_memory.add(observation_msg)
                
                # 6. 记录步骤
                step = ResearchStep(
                    step_number=i + 1,
                    thought=thought,
                    action=action,
                    observation=observation
                )
                research_result.steps.append(step)
                
                # 7. 检查是否结束
                if action.get("tool_name") == "FINISH":
                    logger.info(f"ReAct cycle completed after {i+1} steps")
                    research_result.status = ToolExecutionStatus.SUCCESS
                    research_result.final_answer = observation
                    research_result.steps_taken = i + 1
                    return research_result
                
            except Exception as e:
                logger.error(f"ReAct step {i+1} failed: {e}", exc_info=True)
                # 将错误信息存入记忆中
                error_msg = Message(
                    content=f"Step {i+1} failed with error: {str(e)}"
                )
                task_memory.add(error_msg)
                
                # 如果是LLM相关错误，提前终止循环
                if "Vertex_ai_betaException" in str(e) or "APIConnectionError" in str(e) or "ConnectionError" in str(e):
                    research_result.reason = f"LLM connection failed: {str(e)}"
                    research_result.final_answer = "Research failed due to LLM connection issues"
                    return research_result
        
        # 达到最大循环次数仍未完成
        research_result.steps_taken = max_loops
        return research_result
    
    def _build_react_prompt(self, query: str, tools_info: Dict[str, str], scratchpad: str) -> str:
        """构建ReAct循环的提示词"""
        # 构造系统提示词
        base_system_prompt = self.config.prompt_templates.get('base_system_prompt', 
            "You are an expert research assistant using a ReAct (Reasoning + Action) framework.")
        
        system_prompt = base_system_prompt.format(
            original_goal=query,
            available_tools="\n".join([f"{name}: {desc}" for name, desc in tools_info.items()])
        )
        
        # 构造工具指令
        tool_instruction_template = self.config.prompt_templates.get('tool_instruction_template', 
            "**Available Tools:**\n{available_tools}\n\n**Important Notes for Tool Usage:**\n- When using the 'resolve-library-id' tool, you MUST provide the 'libraryName' argument.\n- When using the 'get-library-docs' tool, you MUST provide the 'context7CompatibleLibraryID' argument.\n- When you have gathered sufficient information, use the FINISH tool with your analysis result.")
        
        tool_instruction = tool_instruction_template.format(
            available_tools="\n".join([f"- Tool: `{name}` (from server: context7)\nDescription: {desc}" for name, desc in tools_info.items()])
        )
        
        return REACT_PROMPT.format(
            system_prompt=system_prompt,
            tool_instruction=tool_instruction,
            scratchpad=scratchpad
        )
    
    def _parse_thought_action(self, decision_str: str, attempt: int = 1) -> Tuple[str, Dict[str, Any]]:
        """解析LLM的决策字符串，提取thought和action"""
        
        # 清理和预处理输入
        decision_str = self._preprocess_decision_string(decision_str)
        
        # 尝试多种解析策略
        parsing_strategies = self._get_parsing_strategies()
        
        for strategy_name, strategy_func in parsing_strategies:
            try:
                logger.debug(f"Attempting parsing strategy: {strategy_name}")
                thought, action = strategy_func(decision_str)
                if self._validate_parsed_result(thought, action):
                    logger.debug(f"Successfully parsed using {strategy_name}")
                    return thought, action
            except Exception as e:
                logger.debug(f"Strategy {strategy_name} failed: {e}")
                continue
        
        # 如果所有策略都失败，尝试重试
        if attempt < self.config.max_parsing_attempts:
            logger.warning(f"Attempt {attempt} failed, retrying...")
            import time
            time.sleep(0.5 * attempt)
            return self._parse_thought_action(decision_str, attempt + 1)
        
        # 所有尝试都失败，返回默认值
        logger.error(f"All parsing strategies failed after {self.config.max_parsing_attempts} attempts")
        return "I need more information to proceed", {"tool_name": "FINISH", "tool_args": {"result": "Unable to parse response"}}
    
    def _preprocess_decision_string(self, decision_str: str) -> str:
        """预处理决策字符串"""
        if not decision_str:
            return "{}"
        
        # 移除markdown代码块标记
        decision_str = re.sub(r'```json\s*', '', decision_str)
        decision_str = re.sub(r'\s*```', '', decision_str)
        
        # 移除不可见字符
        decision_str = decision_str.strip()
        decision_str = decision_str.replace('\ufeff', '')
        decision_str = decision_str.replace('\u200b', '')
        
        # 特殊处理：修复双引号问题
        # 简化策略：直接处理所有重复双引号的情况
        
        # 1. 首先处理最简单的情况：全局替换 ""key"" 为 "key"
        decision_str = re.sub(r'"{2}([^"]+)"{2}', r'"\1"', decision_str)
        decision_str = re.sub(r'"{3}([^"]+)"{3}', r'"\1"', decision_str)
        
        # 2. 修复单引号包裹的键名 ('key' -> "key")
        decision_str = re.sub(r"'([^']+)'(\s*:)", r'"\1"\2', decision_str)
        
        # 3. 特殊处理：如果修复后仍然有重复双引号问题，进行更精细的处理
        # 检查是否还有未解决的重复双引号
        if '""' in decision_str:
            # 处理键位置的重复双引号
            decision_str = re.sub(r'"{2,3}([^"]+)"{2,3}(\s*:)', r'"\1"\2', decision_str)
            # 处理值位置的重复双引号
            decision_str = re.sub(r':\s*"{2,3}([^"]+)"{2,3}(\s*[,}])', r': "\1"\2', decision_str)
        
        # 替换常见的JSON格式问题
        decision_str = decision_str.replace("'", '"')
        decision_str = re.sub(r',\s*}', '}', decision_str)
        decision_str = re.sub(r',\s*]', ']', decision_str)
        
        # 确保action对象正确格式化
        # 更简单直接的方法：全局替换所有重复双引号问题
        # 修复任何位置的 ""key"" 模式为 "key"
        decision_str = re.sub(r'"{2}([^"]+)"{2}', r'"\1"', decision_str)
        # 修复任何位置的 """key""" 模式为 "key"
        decision_str = re.sub(r'"{3}([^"]+)"{3}', r'"\1"', decision_str)
        
        # 特殊处理：修复可能的误匹配，确保不在字符串内容中替换
        # 只替换在键位置的双引号（后跟冒号）
        decision_str = re.sub(r'"{2,3}([^"]+)"{2,3}(\s*:)', r'"\1"\2', decision_str)
        # 只替换在值位置的双引号（前跟冒号）
        decision_str = re.sub(r':\s*"{2,3}([^"]+)"{2,3}(\s*[,}])', r': "\1"\2', decision_str)
        
        return decision_str
    
    def _get_parsing_strategies(self) -> List[Tuple[str, callable]]:
        """获取解析策略列表"""
        return [
            ("code_parser", self._strategy_code_parser),
            ("mixed_text_json", self._strategy_mixed_text_json),
            ("action_patterns", self._strategy_action_patterns),
            ("manual_text_format", self._strategy_manual_text_format),
            ("simple_text_parsing", self._strategy_simple_text_parsing),
            ("fallback_json", self._strategy_fallback_json),
        ]
    
    def _strategy_code_parser(self, decision_str: str) -> Tuple[str, Dict[str, Any]]:
        """策略1: 使用CodeParser解析"""
        try:
            # 首先尝试直接解析JSON（如果内容已经是纯JSON）
            try:
                decision = json.loads(decision_str)
                thought = decision.get("thought", "")
                action = decision.get("action", {})
                return thought, action
            except json.JSONDecodeError:
                pass
            
            # 如果直接解析失败，尝试使用CodeParser
            # 但在使用CodeParser之前先检查文本是否包含代码块标记
            if "```" in decision_str:
                decision_json_str = CodeParser.parse_code(text=decision_str)
                if decision_json_str != decision_str:
                    decision = json.loads(decision_json_str)
                    thought = decision.get("thought", "")
                    action = decision.get("action", {})
                    return thought, action
            else:
                # 如果没有代码块标记，直接返回原文本进行JSON解析
                # 这避免了CodeParser在处理纯JSON时记录不必要的错误
                try:
                    decision = json.loads(decision_str)
                    thought = decision.get("thought", "")
                    action = decision.get("action", {})
                    return thought, action
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            raise ValueError(f"CodeParser failed: {e}")
        
        raise ValueError("CodeParser found no JSON")
    
    def _strategy_mixed_text_json(self, decision_str: str) -> Tuple[str, Dict[str, Any]]:
        """策略2: 从混合文本中提取JSON"""
        json_match = self._extract_json_from_mixed_text(decision_str)
        if not json_match:
            raise ValueError("No JSON found in mixed text")
        
        decision = json.loads(json_match)
        
        if "thought" in decision and "action" in decision:
            thought = decision.get("thought", "")
            action = decision.get("action", {})
            return thought, action
        elif "tool_name" in decision:
            thought = self._extract_thought_from_text(decision_str, json_match)
            action = decision
            return thought, action
        
        raise ValueError("Extracted JSON doesn't contain expected fields")
    
    def _strategy_action_patterns(self, decision_str: str) -> Tuple[str, Dict[str, Any]]:
        """策略3: 从模式中提取action"""
        action_match = self._extract_action_from_patterns(decision_str)
        if not action_match:
            raise ValueError("No action patterns found")
        
        action = json.loads(action_match)
        thought = self._extract_thought_from_text(decision_str, action_match)
        return thought, action
    
    def _strategy_manual_text_format(self, decision_str: str) -> Tuple[str, Dict[str, Any]]:
        """策略4: 手动文本格式解析"""
        lines = decision_str.split('\n')
        thought = ""
        action_str = ""
        
        # 提取thought
        for line in lines:
            line = line.strip()
            if line.lower().startswith('thought:'):
                thought = line[len('Thought:'):].strip()
                break
        
        # 提取action
        action_patterns = [
            r'^Action:\s*(\{.*\})$',
            r'^.*Action:\s*(\{.*\})$',
            r'^(\{.*"tool_name".*\})$'
        ]
        
        for line in lines:
            line = line.strip()
            for pattern in action_patterns:
                match = re.match(pattern, line, re.DOTALL)
                if match:
                    action_str = match.group(1)
                    try:
                        action = json.loads(action_str)
                        return thought, action
                    except json.JSONDecodeError:
                        pass
        
        raise ValueError("No action found in manual parsing")
    
    def _strategy_simple_text_parsing(self, decision_str: str) -> Tuple[str, Dict[str, Any]]:
        """策略6: 简单文本解析，适用于不支持工具调用的模型"""
        # 清理字符串
        clean_str = decision_str.strip()
        
        # 处理代码块格式的JSON
        if clean_str.startswith("```json") and clean_str.endswith("```"):
            json_str = clean_str[7:-3].strip()
            try:
                decision = json.loads(json_str)
                thought = decision.get("thought", "Processing request")
                action = decision.get("action", {"tool_name": "FINISH", "tool_args": {"result": "Processing completed"}})
                return thought, action
            except json.JSONDecodeError:
                pass
        
        # 如果看起来像JSON但解析失败，返回一个简单的完成动作
        if clean_str.startswith('{') and clean_str.endswith('}'):
            # 尝试提取thought内容
            thought_match = re.search(r'[Tt]hought["\s:]*["\']?([^"\n\r]+)', clean_str)
            thought = thought_match.group(1) if thought_match else "Processing request"
            
            # 返回一个简单的完成动作，避免依赖工具调用
            return thought, {"tool_name": "FINISH", "tool_args": {"result": f"Response processed: {thought}"}}
        
        # 如果是纯文本，直接完成
        if clean_str and not clean_str.startswith('{'):
            return clean_str, {"tool_name": "FINISH", "tool_args": {"result": clean_str}}
        
        # 默认返回
        return "Continue processing", {"tool_name": "FINISH", "tool_args": {"result": "Processing completed"}}

    def _strategy_fallback_json(self, decision_str: str) -> Tuple[str, Dict[str, Any]]:
        """策略5: 直接JSON解析作为最后手段"""
        decision = json.loads(decision_str.strip())
        thought = decision.get("thought", "")
        action = decision.get("action", {})
        return thought, action
    
    def _validate_parsed_result(self, thought: str, action: Dict[str, Any]) -> bool:
        """验证解析结果"""
        return isinstance(thought, str) and isinstance(action, dict)
    
    def _extract_json_from_mixed_text(self, text: str) -> Optional[str]:
        """从混合文本中提取JSON对象"""
        # 简化版本，查找平衡的大括号
        brace_count = 0
        start_idx = -1
        
        for i, char in enumerate(text):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    json_str = text[start_idx:i+1]
                    try:
                        json.loads(json_str)
                        return json_str
                    except json.JSONDecodeError:
                        continue
        
        return None
    
    def _extract_action_from_patterns(self, text: str) -> Optional[str]:
        """从常见模式中提取Action JSON"""
        patterns = [
            r'Action:\s*(\{[^}]*\})',
            r'\{[^}]*"tool_name"[^}]*\}',
            r'\{[^}]*"tool_name"\s*:\s*"FINISH"[^}]*\}'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_thought_from_text(self, text: str, json_part: str) -> str:
        """从文本中提取thought"""
        text_without_json = text.replace(json_part, '').strip()
        
        # 查找thought模式
        thought_patterns = [
            r'Thought:\s*(.*?)(?=\nAction:|\n\n|$)',
            r'(?:Step\s*\d+:\s*)?Thought:\s*(.*?)(?=\nAction:|\n\n|$)'
        ]
        
        for pattern in thought_patterns:
            match = re.search(pattern, text_without_json, re.DOTALL | re.IGNORECASE)
            if match:
                thought = match.group(1).strip()
                return re.sub(r'^Step\s*\d+:\s*Thought:\s*', '', thought, flags=re.IGNORECASE)
        
        # Fallback: 返回Action部分之前的文本
        lines = text_without_json.split('\n')
        thought_lines = []
        for line in lines:
            line = line.strip()
            if line.lower().startswith('action:'):
                break
            if line and not line.lower().startswith('step'):
                thought_lines.append(line)
        
        return ' '.join(thought_lines).strip()
    
    async def _execute_tool_action(self, action: Dict[str, Any], query: str) -> str:
        """执行工具行动"""
        tool_name = action.get("tool_name")
        tool_args = action.get("tool_args", {})
        
        if tool_name == "FINISH":
            return tool_args.get("result", "Task completed.")
        
        # 获取mcp_manager，确保安全访问
        mcp_manager = None
        if hasattr(self, 'context') and self.context is not None:
            if hasattr(self.context, 'mcp_manager') and self.context.mcp_manager is not None:
                mcp_manager = self.context.mcp_manager
        
        # 如果无法从context获取，尝试从parent action获取
        if mcp_manager is None and hasattr(self, '_parent_action') and self._parent_action is not None:
            if hasattr(self._parent_action, 'context') and self._parent_action.context is not None:
                if hasattr(self._parent_action.context, 'mcp_manager') and self._parent_action.context.mcp_manager is not None:
                    mcp_manager = self._parent_action.context.mcp_manager
        
        if tool_name in ["resolve-library-id", "get-library-docs"]:
            # Context7 MCP工具调用
            if mcp_manager is None:
                return "Error: MCP manager not available for Context7 tools"
            return await self.tool_service.execute_tool(action, mcp_manager, query)
        elif tool_name == "use_internal_rag":
            # 内部RAG搜索
            result = await self.rag_service.search(query)
            return json.dumps(result.__dict__, ensure_ascii=False)
        else:
            # 其他工具调用
            if mcp_manager is None:
                return f"Error: MCP manager not available for tool '{tool_name}'"
            return await self.tool_service.execute_tool(action, mcp_manager, query)
    
    def _parse_tool_descriptions(self, tool_descriptions: str) -> Dict[str, str]:
        """解析工具描述字符串"""
        tools = {}
        lines = tool_descriptions.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line and ':' in line:
                # 尝试提取工具名称和描述
                if 'Tool:' in line:
                    # 格式: Tool: `tool_name` (from server: context7) Description: ...
                    parts = line.split('Description:', 1)
                    if len(parts) == 2:
                        desc_part = parts[0].strip()
                        desc = parts[1].strip()
                        
                        # 提取工具名称
                        tool_name_match = re.search(r'`([^`]+)`', desc_part)
                        if tool_name_match:
                            tool_name = tool_name_match.group(1)
                            tools[tool_name] = desc
        
        return tools
    
    async def _ask_llm(self, prompt: str) -> str:
        """调用LLM"""
        # 首先尝试使用Research action自己的LLM（由base_role设置）
        research_action = getattr(self, '_parent_action', None)
        if research_action and hasattr(research_action, 'llm') and research_action.llm:
            try:
                return await research_action.llm.aask(prompt)
            except Exception as e:
                logger.warning(f"Failed to use LLM from research_action.llm: {e}")
        
        # 尝试从controller的context获取LLM
        if hasattr(self, 'context') and self.context is not None:
            # 检查context是否有llm属性
            if hasattr(self.context, 'llm') and self.context.llm is not None:
                try:
                    return await self.context.llm.aask(prompt)
                except Exception as e:
                    logger.warning(f"Failed to use LLM from context.llm: {e}")
            
            # 检查context是否有action属性，可能包含llm
            if hasattr(self.context, 'action') and self.context.action is not None:
                if hasattr(self.context.action, 'llm') and self.context.action.llm is not None:
                    try:
                        return await self.context.action.llm.aask(prompt)
                    except Exception as e:
                        logger.warning(f"Failed to use LLM from context.action.llm: {e}")
        
        # 尝试从全局配置获取LLM
        try:
            from metagpt.config2 import Config
            from metagpt.provider.llm_provider_registry import create_llm_instance
            config = Config()
            if hasattr(config, 'llm') and config.llm:
                llm = create_llm_instance(config.llm)
                return await llm.aask(prompt)
        except Exception as e:
            logger.debug(f"Failed to create LLM from global config: {e}")
        
        # 如果没有LLM可用，抛出异常让ReAct cycle处理
        raise ConnectionError("No LLM available for ReAct cycle")


class ResearchSerializer:
    """自定义序列化器，用于处理Research Action的输入输出"""
    
    def serialize_req(self, req: Any, *args, **kwargs) -> str:
        """序列化请求"""
        queries = kwargs.get("queries", [""])
        if isinstance(queries, list) and len(queries) > 0:
            return queries[0]
        return str(queries)
    
    def deserialize_req(self, req: str) -> Any:
        """反序列化请求"""
        return {"queries": [req]}
    
    def serialize_resp(self, resp: Any) -> str:
        """序列化响应"""
        try:
            return json.dumps(resp, ensure_ascii=False)
        except Exception:
            return str(resp)
    
    def deserialize_resp(self, resp: str) -> Any:
        """反序列化响应"""
        try:
            return json.loads(resp)
        except json.JSONDecodeError:
            return {"error": "Failed to deserialize response", "raw_response": resp}


class Research(Action):
    """Research Action主类"""
    
    def __init__(self, name: str = "", context: Any = None, llm: Any = None, config: ResearchConfig = None):
        super().__init__(name=name, context=context, llm=llm)
        # Use the config from the parent class or create a new one
        if hasattr(self, 'config') and self.config:
            self.research_config = self.config if isinstance(self.config, ResearchConfig) else ResearchConfig()
        else:
            self.research_config = config or ResearchConfig()
        self.controller = ResearchController(self.research_config)
        
        # 设置parent action引用，以便controller可以访问LLM
        self.controller._parent_action = self
        
        # 设置控制器上下文
        self.controller.set_context(context)
    
    def set_docrag_engine(self, engine):
        """设置RAG引擎"""
        self.controller.set_rag_engine(engine)
    
    @exp_cache(serializer=ResearchSerializer())
    async def run(self, queries: List[str], tool_descriptions: str = "", **kwargs) -> Dict[str, Any]:
        """运行Research Action"""
        return await self.controller.execute_research(queries, tool_descriptions, **kwargs)