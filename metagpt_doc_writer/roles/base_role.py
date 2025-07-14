# /root/metagpt/mgfr/metagpt_doc_writer/roles/base_role.py (最终修正版)

from metagpt.roles import Role
from metagpt.context import Context
from metagpt_doc_writer.mcp.manager import MCPManager
from typing import Dict, List, Optional
from pydantic import Field

class DocWriterBaseRole(Role):
    # mcp_bindings 仍然是角色特定的，所以保留
    mcp_bindings: Dict[str, List[str]] = Field(default_factory=dict, exclude=True)
    # 【核心修正】将 mcp_manager 声明为 Role 的一个可选字段
    mcp_manager: Optional[MCPManager] = Field(default=None, exclude=True)

    def __init__(self, **kwargs):
        # Pydantic会自动处理kwargs中的'context', 'mcp_manager', 'mcp_bindings'
        super().__init__(**kwargs)

    def can_use_mcp_tool(self, tool_name: str) -> bool:
        # 这里的逻辑不变，它现在直接访问 self.mcp_manager
        if not self.mcp_manager or not self.mcp_bindings:
            return False
        role_name = self.name
        allowed_servers = self.mcp_bindings.get(role_name, [])
        client = self.mcp_manager.tool_to_client_map.get(tool_name)
        return bool(client and client.name in allowed_servers)