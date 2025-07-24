# hierarchical/roles/base_role.py (The Definitive Final Version)
import random
from typing import Any, List

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.provider.llm_provider_registry import create_llm_instance
# 【核心修正】: 导入 ModelsConfig
from metagpt.configs.models_config import ModelsConfig
from hierarchical.utils import get_llm_pool_for_action

class HierarchicalBaseRole(Role):
    """
    新架构中所有角色的基类。
    新增了一个辅助方法 `_execute_action` 来处理LLM资源池调度。
    """
    async def _execute_action(self, action: Action, **kwargs) -> Any:
        """
        使用LLM资源池策略来执行一个Action。
        这个方法将取代直接调用 `action.run()`。
        """
        strategy_config = self.context.kwargs.get("strategy_config", {})
        llm_pool_keys = get_llm_pool_for_action(self.name, action.name, strategy_config)

        original_llm = action.llm
        
        if not llm_pool_keys:
            logger.info(f"Action '{action.name}' (Role: {self.name}) using default LLM.")
            try:
                if action.llm.cost_manager is None:
                    action.llm.cost_manager = self.cost_manager
                return await action.run(**kwargs)
            finally:
                action.llm = original_llm
        
        shuffled_pool = random.sample(llm_pool_keys, len(llm_pool_keys))
        
        # 【核心修正】: 独立加载 ModelsConfig
        models_config = ModelsConfig.default()
        
        for llm_key in shuffled_pool:
            try:
                logger.info(f"Action '{action.name}' (Role: {self.name}) attempting to run with LLM: '{llm_key}'")
                
                # 【核心修正】: 从 models_config 获取配置
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
                
                result = await action.run(**kwargs)
                action.llm = original_llm
                return result
            except Exception as e:
                logger.warning(f"Action '{action.name}' failed with LLM '{llm_key}'. Error: {e}. Trying next fallback...")

        action.llm = original_llm
        logger.error(f"Action '{action.name}' failed with all LLMs in its pool.")
        raise RuntimeError(f"Action '{action.name}' failed exhaustively.")