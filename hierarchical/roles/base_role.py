# mghier/hierarchical/roles/base_role.py (阶段二完成版)

import random
from typing import Any, List

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.provider.llm_provider_registry import create_llm_instance
from metagpt.configs.models_config import ModelsConfig
from hierarchical.utils import get_llm_pool_for_action

class HierarchicalBaseRole(Role):
    """
    新架构中所有角色的基类。
    新增了一个辅助方法 `_execute_action` 来处理LLM资源池调度和MCP工具注入。
    """
    async def _execute_action(self, action: Action, **kwargs) -> Any:
        """
        使用LLM资源池策略来执行一个Action，并注入MCP工具描述。
        这个方法将取代直接调用 `action.run()`。
        """
        # --- 【新增】MCP工具描述注入逻辑 ---
        tool_descriptions = ""
        # 检查 mcp_manager 是否存在且已初始化
        if hasattr(self.context, 'mcp_manager') and self.context.mcp_manager and self.context.mcp_manager.clients:
            # 从全局配置中读取角色绑定信息
            role_bindings = self.context.kwargs.custom_config.get("role_mcp_bindings", {})
            
            # 检查当前角色 (self.name) 是否有绑定
            if self.name in role_bindings:
                bound_servers = role_bindings[self.name]
                logger.debug(f"Role '{self.name}' is bound to MCP servers: {bound_servers}")
                # 注意：目前 get_tools_description 返回所有工具的描述。
                # 如果未来需要只获取特定服务器的工具，需要扩展 MCPManager。
                tool_descriptions = self.context.mcp_manager.get_tools_description()
                logger.info(f"Injecting tool descriptions for Role '{self.name}' into Action '{action.name}'.")
        
        # 将工具描述添加到传递给 action.run 的参数中
        kwargs['tool_descriptions'] = tool_descriptions
        # --- MCP注入逻辑结束 ---

        # --- 现有LLM资源池调度逻辑 (保持不变) ---
        strategy_config = self.context.kwargs.get("strategy_config", {})
        llm_pool_keys = get_llm_pool_for_action(self.name, action.name, strategy_config)

        original_llm = action.llm
        
        if not llm_pool_keys:
            logger.info(f"Action '{action.name}' (Role: {self.name}) using default LLM.")
            try:
                if action.llm.cost_manager is None:
                    action.llm.cost_manager = self.cost_manager
                # 【修改】确保将包含工具描述的kwargs传递下去
                return await action.run(**kwargs)
            finally:
                action.llm = original_llm
        
        shuffled_pool = random.sample(llm_pool_keys, len(llm_pool_keys))
        
        models_config = ModelsConfig.default()
        
        for llm_key in shuffled_pool:
            try:
                logger.info(f"Action '{action.name}' (Role: {self.name}) attempting to run with LLM: '{llm_key}'")
                
                llm_config = models_config.get(llm_key)
                if not llm_config:
                    logger.warning(f"LLM key '{llm_key}' not found in global 'models' configuration. Skipping.")
                    continue
                
                dynamic_llm = create_llm_instance(llm_config)
                if dynamic_llm.cost_manager is None:
                    if hasattr(self.context, '_select_costmanager'):
                         dynamic_llm.cost_manager = self.context._select_costmanager(llm_config)
                    else:
                         dynamic_llm.cost_manager = self.cost_manager
                
                action.llm = dynamic_llm
                
                # 【修改】确保将包含工具描述的kwargs传递下去
                result = await action.run(**kwargs)
                action.llm = original_llm
                return result
            except Exception as e:
                logger.warning(f"Action '{action.name}' failed with LLM '{llm_key}'. Error: {e}. Trying next fallback...")

        action.llm = original_llm
        logger.error(f"Action '{action.name}' failed with all LLMs in its pool.")
        raise RuntimeError(f"Action '{action.name}' failed exhaustively.")