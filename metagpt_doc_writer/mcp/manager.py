# /root/metagpt/mgfr/metagpt_doc_writer/mcp/manager.py (超时可配置版)

import asyncio
import json
from typing import Dict, Any, List

from metagpt.logs import logger
from metagpt_doc_writer.mcp.client import MCPClient

class MCPManager:
    """
    管理所有MCP客户端连接和工具路由。
    这是一个全局服务，为所有Agent提供统一的工具调用接口。
    """
    def __init__(self, server_configs: Dict[str, Any]):
        self.server_configs = server_configs or {}
        self.clients: Dict[str, MCPClient] = {}
        self.tool_to_client_map: Dict[str, MCPClient] = {}

    async def start_servers(self):
        """启动并初始化所有在配置中定义的MCP服务器。"""
        if not self.server_configs:
            logger.info("No MCP servers configured.")
            return
            
        tasks = []
        for name, config in self.server_configs.items():
            command = [config["command"]] + config.get("args", [])
            
            # 【关键修改】从配置中读取超时时间，并提供一个更长的默认值
            timeout = config.get("timeout", 60)
            logger.info(f"Creating MCPClient for '{name}' with a timeout of {timeout}s.")
            
            client = MCPClient(name=name, command=command, timeout=timeout)
            self.clients[name] = client
            tasks.append(client.connect())
        
        await asyncio.gather(*tasks)
        self._map_tools()

    def _map_tools(self):
        """创建从工具名称到对应客户端的映射。"""
        for client_name, client in self.clients.items():
            for tool in client.tools:
                tool_name = tool.get("name")
                if tool_name in self.tool_to_client_map:
                    logger.warning(f"Tool '{tool_name}' is provided by multiple servers. Using server '{client_name}'.")
                self.tool_to_client_map[tool_name] = client

    def get_tools_description(self) -> str:
        """为LLM生成所有可用工具的格式化描述。"""
        if not self.tool_to_client_map:
            return "No external tools available."
        
        descriptions = []
        for tool_name, client in self.tool_to_client_map.items():
            descriptions.append(f"- {tool_name} (from server: {client.name})")
        return "## Available Tools\n" + "\n".join(descriptions)

    async def call_tool(self, tool_name: str, args: dict) -> str:
        """根据工具名称路由并调用工具，返回结果。"""
        logger.info(f"MCPManager received call for tool '{tool_name}' with args: {args}")
        client = self.tool_to_client_map.get(tool_name)
        if not client:
            raise ValueError(f"Tool '{tool_name}' not found in any connected MCP server.")
        
        try:
            result = await client.call_tool(tool_name, args)
            return json.dumps(result.get("content", "Tool executed successfully."))
        except Exception as e:
            logger.error(f"Error calling tool '{tool_name}': {e}")
            return f"Error executing tool '{tool_name}': {e}"

    async def close(self):
        """关闭所有MCP客户端连接。"""
        await asyncio.gather(*(client.close() for client in self.clients.values()))
        logger.info("All MCP connections closed.")