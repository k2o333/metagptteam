# /root/metagpt/mgfr/metagpt_doc_writer/mcp/client.py (超时可配置版)

import asyncio
import json
import uuid
from typing import Dict, Any, List

from metagpt.logs import logger
from metagpt_doc_writer.mcp.transport import StdioTransport

class MCPClient:
    """
    MCP客户端，负责与单个MCP服务器进行通信。
    它处理协议生命周期（初始化、工具调用等）和消息路由。
    """
    # 【关键修改】在构造函数中接收 timeout 参数
    def __init__(self, name: str, command: list[str], timeout: int = 30):
        self.name = name
        self.transport = StdioTransport(command)
        self._msg_handlers: Dict[str, asyncio.Future] = {}
        self._listener_task: asyncio.Task = None
        self.tools: List[Dict[str, Any]] = []
        self.timeout = timeout  # 保存超时时间

    async def connect(self):
        """连接到服务器，启动监听器并执行初始化握手。"""
        await self.transport.connect()
        self._listener_task = asyncio.create_task(self._listen())
        await self._initialize()

    async def _initialize(self):
        """执行MCP初始化握手。"""
        logger.info(f"Initializing connection to MCP server: {self.name}")
        init_params = {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "MetaGPTDocWriterClient", "version": "1.0"},
        }
        response = await self._send_request("initialize", init_params)
        
        server_info = response.get("serverInfo", {})
        logger.info(f"Successfully initialized with server: {server_info.get('name')} (v{server_info.get('version')})")

        await self.transport.send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        
        self.tools = (await self.list_tools()).get("tools", [])
        logger.info(f"Server '{self.name}' provides tools: {[tool['name'] for tool in self.tools]}")

    async def _listen(self):
        """持续从transport读取消息并处理。"""
        try:
            while True:
                line = await self.transport.readline()
                if not line:
                    await asyncio.sleep(0.1)
                    continue
                message = json.loads(line)
                self._handle_message(message)
        except (ConnectionAbortedError, ConnectionResetError) as e:
            logger.warning(f"Connection to '{self.name}' lost: {e}")
        except Exception as e:
            logger.error(f"Error in listener for '{self.name}': {e}", exc_info=True)

    def _handle_message(self, message: dict):
        """分发收到的消息。"""
        msg_id = message.get("id")
        if msg_id in self._msg_handlers:
            future = self._msg_handlers.pop(msg_id)
            if "error" in message:
                future.set_exception(RuntimeError(f"MCP Error: {message['error']}"))
            else:
                future.set_result(message.get("result"))
        else:
            logger.warning(f"Received unhandled message from '{self.name}': {message}")

    async def _send_request(self, method: str, params: dict) -> dict:
        """发送一个请求并等待其响应。"""
        request_id = str(uuid.uuid4())
        future = asyncio.get_event_loop().create_future()
        self._msg_handlers[request_id] = future
        
        message = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        
        await self.transport.send(message)
        
        try:
            # 【关键修改】使用实例变量 self.timeout
            return await asyncio.wait_for(future, timeout=self.timeout)
        except asyncio.TimeoutError:
            self._msg_handlers.pop(request_id, None)
            # 【关键修改】在错误信息中包含超时时长
            raise TimeoutError(f"Request '{method}' to server '{self.name}' timed out after {self.timeout}s.")

    async def list_tools(self) -> dict:
        return await self._send_request("tools/list", {})

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        params = {"name": tool_name, "arguments": arguments}
        return await self._send_request("tools/call", params)

    async def close(self):
        if self._listener_task:
            self._listener_task.cancel()
        await self.transport.close()