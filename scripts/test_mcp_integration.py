# 文件路径: /root/metagpt/mgfr/scripts/test_mcp_integration.py (最终修正版)

import asyncio
import sys
from pathlib import Path
import yaml  # <-- 【关键改动】导入PyYAML库

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# --- 导入我们的模块 ---
from metagpt.logs import logger
from metagpt_doc_writer.mcp.manager import MCPManager

async def test_mcp_manager_integration():
    """
    测试MCPManager能否成功启动、连接服务器、发现并调用工具。
    """
    logger.info("--- 启动 MCP Manager 集成测试 ---")

    # 1. 【关键改动】手动加载我们自定义的配置
    config_path = PROJECT_ROOT / "configs" / "config2.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        custom_config = yaml.safe_load(f)

    mcp_server_configs = custom_config.get("mcp_servers")
    assert mcp_server_configs, "mcp_servers 未在 config2.yaml 中配置或为空"

    # 2. 初始化并启动 MCPManager
    # 直接将我们手动加载的字典传进去
    manager = MCPManager(server_configs=mcp_server_configs)
    await manager.start_servers()

    # 3. 验证工具是否被发现
    logger.info("验证工具发现...")
    assert "web_search" in manager.tool_to_client_map, "工具 'web_search' 未被发现"
    logger.info(f"发现的工具: {list(manager.tool_to_client_map.keys())}")
    logger.info("✅ 工具发现成功")

    # 4. 调用工具并验证结果
    logger.info("调用 'web_search' 工具...")
    query = "MetaGPT in MCP"
    result = await manager.call_tool("web_search", {"query": query})

    logger.info(f"工具返回结果: {result}")
    assert f"Mocked search result for '{query}'" in result
    logger.info("✅ 工具调用与结果返回成功")

    # 5. 关闭管理器
    await manager.close()
    logger.info("✅ MCP Manager 关闭成功")
    logger.info("--- MCP Manager 集成测试通过！ ---")

if __name__ == "__main__":
    asyncio.run(test_mcp_manager_integration())