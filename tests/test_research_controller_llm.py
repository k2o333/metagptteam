#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试ResearchController中LLM访问的修复
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from hierarchical.actions.research_controller import ResearchController, ResearchConfig
from metagpt.config2 import Config
from metagpt.provider.llm_provider_registry import create_llm_instance


async def test_research_controller_llm():
    """测试ResearchController的LLM访问"""
    print("Testing ResearchController LLM access...")
    
    # 创建配置
    config = ResearchConfig()
    
    # 创建LLM实例
    try:
        llm_config = Config()
        llm = create_llm_instance(llm_config.llm) if hasattr(llm_config, 'llm') else None
        print(f"LLM instance created: {llm is not None}")
    except Exception as e:
        print(f"Failed to create LLM instance: {e}")
        llm = None
    
    # 创建ResearchController实例
    controller = ResearchController(config=config, llm=llm)
    print(f"ResearchController created with LLM: {controller.llm is not None}")
    
    # 测试_get_llm_fallback方法
    fallback_llm = controller._get_llm_fallback()
    print(f"Fallback LLM available: {fallback_llm is not None}")
    
    print("Test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_research_controller_llm())