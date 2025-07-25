# mghier/mcp/transport.py

import asyncio
import json
from metagpt.logs import logger

class StdioTransport:
    """
    通过标准输入/输出（stdio）与子进程进行通信的传输层。
    它负责启动服务器进程，并通过其stdin和stdout发送和接收JSON-RPC消息。
    """
    def __init__(self, command: list[str]):
        self.command = command
        self.process: asyncio.subprocess.Process = None

    async def connect(self):
        """启动服务器子进程并建立通信管道。"""
        logger.info(f"Starting MCP server with command: {' '.join(self.command)}")
        try:
            self.process = await asyncio.create_subprocess_shell(
                ' '.join(self.command),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            logger.info(f"MCP server process started with PID: {self.process.pid}")
        except Exception as e:
            logger.error(f"Failed to start MCP server process: {e}", exc_info=True)
            raise

    async def send(self, message: dict):
        """向服务器进程的stdin发送一条JSON-RPC消息。"""
        if not self.process or self.process.stdin.is_closing():
            raise ConnectionError("MCP server process is not running or stdin is closed.")
        
        msg_str = json.dumps(message) + '\n'
        self.process.stdin.write(msg_str.encode('utf-8'))
        await self.process.stdin.drain()

    async def readline(self) -> str:
        """从服务器进程的stdout读取一行消息。"""
        if not self.process or self.process.stdout.at_eof():
            raise ConnectionError("MCP server process is not running or stdout is at EOF.")
        
        line = await self.process.stdout.readline()
        if not line:
            stderr = await self.process.stderr.read()
            logger.error(f"MCP server process terminated unexpectedly. Stderr: {stderr.decode(errors='ignore')}")
            raise ConnectionAbortedError("MCP server process terminated.")
        return line.decode('utf-8')

    async def close(self, timeout: float = 5.0):
        """
        带超时的、更健壮的关闭逻辑。
        关闭与服务器进程的连接并终止进程。
        """
        if not self.process or self.process.returncode is not None:
            logger.info("MCP server process already terminated or not started.")
            return

        logger.info(f"Gracefully terminating MCP server process with PID: {self.process.pid}...")
        
        if not self.process.stdin.is_closing():
            self.process.stdin.close()
            await self.process.stdin.wait_closed()

        self.process.terminate()

        try:
            await asyncio.wait_for(self.process.wait(), timeout=timeout)
            logger.info(f"MCP server process {self.process.pid} terminated gracefully.")
        except asyncio.TimeoutError:
            logger.warning(f"Graceful termination timed out after {timeout}s. Forcing kill...")
            self.process.kill()
            await self.process.wait()
            logger.info(f"MCP server process {self.process.pid} has been forcibly killed.")
        except Exception as e:
            logger.error(f"An error occurred while closing MCP server process: {e}", exc_info=True)