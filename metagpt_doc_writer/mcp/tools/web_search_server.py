# 文件路径: /root/metagpt/mgfr/metagpt_doc_writer/mcp/tools/web_search_server.py (最终修正版)

import asyncio
import json
import sys

async def main():
    """
    一个极简的、遵循MCP协议的异步服务器，用于测试。
    """
    # 【核心修正】: 创建一个异步读取器来包装 sys.stdin
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    
    # 将 sys.stdin 连接到异步协议
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    # 【核心修正】: 创建一个异步写入器来包装 sys.stdout
    writer_transport, writer_protocol = await loop.connect_write_pipe(
        asyncio.streams.FlowControlMixin, sys.stdout
    )
    writer = asyncio.StreamWriter(writer_transport, writer_protocol, None, loop)

    async def write_message(data: dict):
        msg_str = json.dumps(data) + '\n'
        writer.write(msg_str.encode('utf-8'))
        await writer.drain()

    # 初始化握手
    # 【核心修正】: 使用异步读取器
    line_bytes = await reader.readline()
    request = json.loads(line_bytes.decode('utf-8'))
    if request.get("method") == "initialize":
        response = {
            "jsonrpc": "2.0",
            "id": request["id"],
            "result": {
                "protocolVersion": "2025-06-18",
                "serverInfo": {"name": "MockSearchServer", "version": "1.0"},
                "capabilities": {"tools": {}}
            }
        }
        await write_message(response)

    # 等待 initialized 通知 (在真实服务器中会处理，这里简化)
    await reader.readline()

    # 循环处理工具调用
    while not reader.at_eof():
        try:
            line_bytes = await reader.readline()
            if not line_bytes:
                continue
            request = json.loads(line_bytes.decode('utf-8'))
            method = request.get("method")
            
            if method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {"tools": [{"name": "web_search", "description": "A mock web search tool."}]}
                }
            elif method == "tools/call" and request["params"]["name"] == "web_search":
                query = request["params"]["arguments"].get("query", "N/A")
                response = {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {"content": [{"type": "text", "text": f"Mocked search result for '{query}'"}]}
                }
            else:
                response = {"jsonrpc": "2.0", "id": request["id"], "error": {"code": -32601, "message": "Method not found"}}
            
            await write_message(response)
        except (json.JSONDecodeError, asyncio.IncompleteReadError):
            continue # 忽略格式不正确的行或不完整的读取
        except Exception:
            break

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass