# mghier/hierarchical/actions/research_service.py (Context7 MCP和工具执行服务)

import json
import time
from typing import Dict, Any, List, Optional, Tuple
from metagpt.logs import logger

from .research_model import (
    ToolExecutionStatus, ToolExecutionResult, LibraryResolutionResult,
    Context7ToolConfig, ResearchConfig
)


class Context7MCPService:
    """Context7 MCP服务集成类"""
    
    def __init__(self, config: Context7ToolConfig):
        self.config = config
    
    async def resolve_library_id(self, mcp_manager, library_name: str) -> LibraryResolutionResult:
        """解析库ID，使用Context7最佳实践"""
        logger.info(f"Resolving library ID for: '{library_name}'")
        
        # 检查是否是已知的库ID格式
        if self._is_valid_library_id_format(library_name):
            return LibraryResolutionResult(
                library_name=library_name,
                resolved_id=library_name,
                description="Direct library ID provided"
            )
        
        # 尝试从常见库名称映射中获取
        mapped_id = self.config.common_library_names.get(library_name.lower())
        if mapped_id:
            return LibraryResolutionResult(
                library_name=library_name,
                resolved_id=mapped_id,
                description="Mapped from common library name"
            )
        
        # 调用MCP工具解析
        try:
            result_str = await mcp_manager.call_tool("resolve-library-id", {"libraryName": library_name})
            result_content = json.loads(result_str)
            
            # 解析返回的结果
            return self._parse_resolve_result(library_name, result_content)
            
        except Exception as e:
            logger.error(f"Failed to resolve library ID for '{library_name}': {e}")
            return LibraryResolutionResult(
                library_name=library_name,
                error=str(e)
            )
    
    async def get_library_docs(self, mcp_manager, library_id: str, topic: Optional[str] = None, 
                              tokens: Optional[int] = None) -> ToolExecutionResult:
        """获取库文档，使用Context7最佳实践"""
        logger.info(f"Getting library docs for: '{library_id}' with topic: '{topic}'")
        
        # 构建参数
        args = {"context7CompatibleLibraryID": library_id}
        if topic:
            args["topic"] = topic
        if tokens and tokens > 0:
            args["tokens"] = tokens
        else:
            args["tokens"] = self.config.max_tokens_default
        
        try:
            result_str = await mcp_manager.call_tool("get-library-docs", args)
            result_content = json.loads(result_str)
            
            return ToolExecutionResult(
                status=ToolExecutionStatus.SUCCESS,
                source=f"mcp_tool:get-library-docs",
                raw_data=result_content
            )
            
        except Exception as e:
            logger.error(f"Failed to get library docs for '{library_id}': {e}")
            return ToolExecutionResult(
                status=ToolExecutionStatus.FAILURE,
                source=f"mcp_tool:get-library-docs",
                reason=str(e)
            )
    
    def _is_valid_library_id_format(self, library_id: str) -> bool:
        """检查是否是有效的库ID格式"""
        return (
            library_id.startswith("/") and 
            library_id.count("/") >= 2 and
            len(library_id.split("/")) >= 3
        )
    
    def _parse_resolve_result(self, library_name: str, result_content: Any) -> LibraryResolutionResult:
        """解析resolve-library-id的结果"""
        try:
            # 检查结果格式
            if isinstance(result_content, list) and len(result_content) > 0:
                # 假设第一个结果是最佳匹配
                first_result = result_content[0]
                if isinstance(first_result, dict):
                    return LibraryResolutionResult(
                        library_name=library_name,
                        resolved_id=first_result.get("Context7-compatible library ID"),
                        trust_score=first_result.get("Trust Score"),
                        code_snippets=first_result.get("Code Snippets"),
                        description=first_result.get("Description")
                    )
            
            # 如果无法解析，尝试其他格式
            if isinstance(result_content, dict):
                return LibraryResolutionResult(
                    library_name=library_name,
                    resolved_id=result_content.get("library_id") or result_content.get("id"),
                    trust_score=result_content.get("trust_score"),
                    code_snippets=result_content.get("code_snippets"),
                    description=result_content.get("description")
                )
            
            # 无法解析
            return LibraryResolutionResult(
                library_name=library_name,
                error="Unable to parse resolve result"
            )
            
        except Exception as e:
            logger.error(f"Failed to parse resolve result: {e}")
            return LibraryResolutionResult(
                library_name=library_name,
                error=f"Parse error: {str(e)}"
            )


class ToolExecutionService:
    """工具执行服务"""
    
    def __init__(self, config: ResearchConfig):
        self.config = config
        self.context7_service = Context7MCPService(config.context7_config)
        # 获取工具重试配置
        self.tool_retry_config = config.tool_retry_config or {
            "max_retry_attempts": 3,
            "retry_models": ["gemini-2.0-flash", "glm4f", "magistral-medium", "Qwen3-8B"]
        }
    
    async def execute_tool(self, action: Dict[str, Any], mcp_manager, query: str) -> str:
        """执行工具调用，包含Context7智能处理"""
        tool_name = action.get("tool_name")
        tool_args = action.get("tool_args", {})
        
        if tool_name == "FINISH":
            return action.get("result", "Task completed.")
        
        logger.info(f"Executing tool '{tool_name}' with args: {tool_args}")
        start_time = time.time()
        
        # 尝试执行工具，包含重试机制
        max_retry_attempts = self.tool_retry_config.get("max_retry_attempts", 3)
        retry_models = self.tool_retry_config.get("retry_models", [])
        
        for attempt in range(max_retry_attempts):
            try:
                # 工具验证
                validation_result = self._validate_tool_execution(tool_name, tool_args, mcp_manager)
                if not validation_result["valid"]:
                    return validation_result["error"]
                
                # Context7特殊处理
                if tool_name == "resolve-library-id":
                    library_name = tool_args.get("libraryName", "")
                    if not library_name:
                        # 如果没有提供库名称，尝试从查询中提取
                        library_name = self._extract_library_name_from_query(query)
                    
                    result = await self.context7_service.resolve_library_id(mcp_manager, library_name)
                    return json.dumps(result.__dict__, ensure_ascii=False)
                
                elif tool_name == "get-library-docs":
                    library_id = tool_args.get("context7CompatibleLibraryID", "")
                    topic = tool_args.get("topic")
                    tokens = tool_args.get("tokens")
                    
                    # 如果没有提供库ID，尝试先解析
                    if not library_id:
                        library_name = self._extract_library_name_from_query(query)
                        if library_name:
                            resolve_result = await self.context7_service.resolve_library_id(mcp_manager, library_name)
                            if resolve_result.is_success():
                                library_id = resolve_result.resolved_id
                    
                    if library_id:
                        result = await self.context7_service.get_library_docs(mcp_manager, library_id, topic, tokens)
                        execution_time = time.time() - start_time
                        logger.info(f"Tool execution completed in {execution_time:.2f}s")
                        return json.dumps(result.__dict__, ensure_ascii=False)
                    else:
                        return "Error: Cannot determine library ID for get-library-docs. Please provide a valid library ID or library name."
                
                # 其他工具调用
                result_str = await mcp_manager.call_tool(tool_name, tool_args)
                execution_time = time.time() - start_time
                logger.info(f"Tool execution completed in {execution_time:.2f}s")
                return result_str
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Tool '{tool_name}' execution failed after {execution_time:.2f}s: {e}")
                
                # 如果不是最后一次尝试，记录重试信息
                if attempt < max_retry_attempts - 1:
                    logger.info(f"Retrying tool '{tool_name}' (attempt {attempt + 1}/{max_retry_attempts})")
                    # 可以在这里添加延迟或其他重试逻辑
                    continue
                else:
                    return f"Error executing tool '{tool_name}' after {max_retry_attempts} attempts: {str(e)}"
    
    def _validate_tool_execution(self, tool_name: str, tool_args: Dict[str, Any], mcp_manager) -> Dict[str, Any]:
        """验证工具执行"""
        result = {"valid": True, "error": ""}
        
        if not self.config.tool_validation_enabled:
            return result
        
        # 检查工具是否可用
        if not hasattr(mcp_manager, 'tool_to_client_map') or tool_name not in mcp_manager.tool_to_client_map:
            result["valid"] = False
            result["error"] = f"Tool '{tool_name}' is not available."
            if self.config.provide_alternatives:
                available_tools = list(mcp_manager.tool_to_client_map.keys()) if hasattr(mcp_manager, 'tool_to_client_map') else []
                result["error"] += f" Available tools are: {available_tools}"
            return result
        
        # 特定工具参数验证
        if tool_name == "resolve-library-id":
            if not tool_args.get("libraryName"):
                result["valid"] = False
                result["error"] = "Tool 'resolve-library-id' requires 'libraryName' argument."
        
        elif tool_name == "get-library-docs":
            if not tool_args.get("context7CompatibleLibraryID"):
                result["valid"] = False
                result["error"] = "Tool 'get-library-docs' requires 'context7CompatibleLibraryID' argument."
        
        return result
    
    def _extract_library_name_from_query(self, query: str) -> str:
        """从查询中提取库名称"""
        import re
        
        # 常见库模式
        library_patterns = [
            r'([a-zA-Z][a-zA-Z0-9]*)\s+(library|framework|package|module)',
            r'([a-zA-Z][a-zA-Z0-9]*)\s+docs?',
            r'([a-zA-Z][a-zA-Z0-9]*)\s+documentation',
            r'([a-zA-Z][a-zA-Z0-9]*)\s+api',
            r'([a-zA-Z][a-zA-Z0-9]*)\s+guide',
            r'([a-zA-Z][a-zA-Z0-9]*)\s+tutorial',
            r'about\s+([a-zA-Z][a-zA-Z0-9]*)',
            r'learn\s+([a-zA-Z][a-zA-Z0-9]*)',
            r'how\s+to\s+use\s+([a-zA-Z][a-zA-Z0-9]*)',
        ]
        
        for pattern in library_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                library_name = match.group(1).lower()
                # 检查是否是已知的库名称
                if library_name in self.config.context7_config.common_library_names:
                    return library_name
                # 如果不是已知的，返回提取的名称
                return library_name
        
        # 如果没有匹配到，尝试从查询中找到主要的技术名词
        words = query.split()
        for word in words:
            word = word.strip('.,?!;:()[]{}"\'')
            if word.lower() in self.config.context7_config.common_library_names:
                return word.lower()
        
        return ""


class InternalRAGService:
    """内部RAG服务"""
    
    def __init__(self, rag_engine=None):
        self.rag_engine = rag_engine
    
    async def search(self, query: str, top_k: int = 3) -> ToolExecutionResult:
        """搜索内部RAG"""
        logger.info(f"Searching internal DocRAG for query: '{query}'")
        
        if not self.rag_engine:
            return ToolExecutionResult(
                status=ToolExecutionStatus.FAILURE,
                source="internal_docrag",
                reason="Engine not initialized"
            )
        
        try:
            retrieved_nodes = await self.rag_engine.asearch(query, top_k=top_k)
            retrieved_content = [node.get_content() for node in retrieved_nodes]
            
            return ToolExecutionResult(
                status=ToolExecutionStatus.SUCCESS,
                source="internal_docrag",
                raw_data={"retrieved_data": retrieved_content}
            )
            
        except Exception as e:
            logger.error(f"Internal RAG search failed: {e}")
            return ToolExecutionResult(
                status=ToolExecutionStatus.FAILURE,
                source="internal_docrag",
                reason=str(e)
            )