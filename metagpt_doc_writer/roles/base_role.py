# /root/metagpt/mgfr/metagpt_doc_writer/roles/base_role.py (最终版)
from typing import Optional, Dict, List
from pydantic import Field
from metagpt.roles import Role
from metagpt.utils.project_repo import ProjectRepo
from metagpt_doc_writer.mcp.manager import MCPManager
# 注意：Action的定义不应放在这里，而应放在各自的文件中或actions/目录下

class DocWriterBaseRole(Role):
    repo: Optional[ProjectRepo] = Field(default=None, exclude=True)
    llm_activation: Dict[str, bool] = Field(default_factory=dict, exclude=True)
    mcp_manager: Optional[MCPManager] = Field(default=None, exclude=True)
    mcp_bindings: Dict[str, List[str]] = Field(default_factory=dict, exclude=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.llm_activation = kwargs.get("llm_activation", {})
        self.mcp_manager = kwargs.get("mcp_manager")
        self.mcp_bindings = kwargs.get("mcp_bindings", {})

    def can_use_mcp_tool(self, tool_name: str) -> bool:
        """检查当前角色是否有权限使用某个MCP工具"""
        if not self.mcp_manager or not self.mcp_bindings:
            return False
        
        role_name = self.__class__.__name__
        allowed_servers = self.mcp_bindings.get(role_name, [])
        
        client = self.mcp_manager.tool_to_client_map.get(tool_name)
        if client and client.name in allowed_servers:
            return True
        
        return False