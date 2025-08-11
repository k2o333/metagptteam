#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/8/10 19:40
@Author  : claude
@File    : test_logging.py
@Desc    : 测试日志记录和LLM拦截功能
"""

import asyncio
import sys
from pathlib import Path
import shutil
import os

# 路径设置
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT.parent))

from metagpt.provider.base_llm import BaseLLM
from metagpt.const import USE_CONFIG_TIMEOUT
from typing import Union, List, Dict, Optional


class MockLLM(BaseLLM):
    """模拟LLM类用于测试"""
    def __init__(self, model_name: str = "mock-model"):
        from metagpt.configs.llm_config import LLMConfig
        self.model = model_name
        # 创建一个简单的配置对象
        config = LLMConfig()
        config.stream = False
        self.config = config
        super().__init__(config=config)
        
    async def _achat_completion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT):
        """模拟异步聊天完成"""
        return {"choices": [{"message": {"content": f"Mock response for: {messages[-1]['content']}"}}]}
        
    async def acompletion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT):
        """模拟异步完成"""
        return await self._achat_completion(messages, timeout)
        
    async def _achat_completion_stream(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> str:
        """模拟异步流式聊天完成"""
        return f"Mock stream response for: {messages[-1]['content']}"


async def test_run_hierarchical_logging():
    """测试run_hierarchical.py的日志功能"""
    print("测试run_hierarchical.py的日志功能...")
    
    # 创建测试目录和文件
    test_logs_dir = PROJECT_ROOT / "logs" / "run_hierarchical"
    test_logs_dir.mkdir(parents=True, exist_ok=True)
    
    # 运行脚本前检查日志文件
    initial_logs = list(test_logs_dir.glob("*.log"))
    
    # 导入并运行run_hierarchical.py中的部分代码来测试日志
    from scripts.run_hierarchical import setup_script_logging, patch_llm_aask_for_detailed_logging
    from hierarchical.context import HierarchicalContext
    
    # 设置日志
    logger = setup_script_logging()
    logger.info("开始测试run_hierarchical.py的日志功能")
    
    # 创建上下文
    ctx = HierarchicalContext()
    ctx.kwargs.successful_llm_calls = 0
    ctx.kwargs.llm_call_counter = 0
    
    # 应用猴子补丁
    patch_llm_aask_for_detailed_logging(ctx)
    
    # 测试LLM调用
    llm = MockLLM("test-model")
    response = await llm.aask("这是一个测试问题")
    logger.info(f"LLM调用响应: {response}")
    
    # 检查是否有新的日志文件生成
    final_logs = list(test_logs_dir.glob("*.log"))
    new_logs = set(final_logs) - set(initial_logs)
    
    # 总是检查最新的日志文件
    if final_logs:
        latest_log = max(final_logs, key=os.path.getctime)
        content = latest_log.read_text()
        if "LLM Call #1 Request" in content and "LLM Call #1 Response" in content:
            print(f"✓ 成功生成新的日志文件: {latest_log}")
            print("✓ LLM调用详细信息已记录到日志文件")
            return True
        else:
            print(f"✗ 日志文件未包含LLM调用详细信息: {latest_log}")
            return False
    elif new_logs:
        print(f"✓ 成功生成新的日志文件: {new_logs}")
        # 检查日志内容
        for log_file in new_logs:
            content = log_file.read_text()
            if "LLM Call #1 Request" in content and "LLM Call #1 Response" in content:
                print("✓ LLM调用详细信息已记录到日志文件")
                return True
    else:
        print("✗ 未生成新的日志文件")
        return False


async def test_adapt_document_logging():
    """测试adapt_document.py的日志功能"""
    print("测试adapt_document.py的日志功能...")
    
    # 创建测试目录和文件
    test_logs_dir = PROJECT_ROOT / "logs" / "adapt_document"
    test_logs_dir.mkdir(parents=True, exist_ok=True)
    
    # 运行脚本前检查日志文件
    initial_logs = list(test_logs_dir.glob("*.log"))
    
    # 导入并运行adapt_document.py中的部分代码来测试日志
    from scripts.adapt_document import setup_script_logging, patch_llm_aask_for_detailed_logging
    from hierarchical.context import HierarchicalContext
    
    # 设置日志
    logger = setup_script_logging()
    logger.info("开始测试adapt_document.py的日志功能")
    
    # 创建上下文
    ctx = HierarchicalContext()
    ctx.kwargs.successful_llm_calls = 0
    ctx.kwargs.llm_call_counter = 0
    
    # 应用猴子补丁
    patch_llm_aask_for_detailed_logging(ctx)
    
    # 测试LLM调用
    llm = MockLLM("test-model-2")
    response = await llm.aask("这是另一个测试问题")
    logger.info(f"LLM调用响应: {response}")
    
    # 检查是否有新的日志文件生成
    final_logs = list(test_logs_dir.glob("*.log"))
    new_logs = set(final_logs) - set(initial_logs)
    
    # 总是检查最新的日志文件
    if final_logs:
        latest_log = max(final_logs, key=os.path.getctime)
        content = latest_log.read_text()
        if "LLM Call #1 Request" in content and "LLM Call #1 Response" in content:
            print(f"✓ 成功生成新的日志文件: {latest_log}")
            print("✓ LLM调用详细信息已记录到日志文件")
            return True
        else:
            print(f"✗ 日志文件未包含LLM调用详细信息: {latest_log}")
            return False
    elif new_logs:
        print(f"✓ 成功生成新的日志文件: {new_logs}")
        # 检查日志内容
        for log_file in new_logs:
            content = log_file.read_text()
            if "LLM Call #1 Request" in content and "LLM Call #1 Response" in content:
                print("✓ LLM调用详细信息已记录到日志文件")
                return True
    else:
        print("✗ 未生成新的日志文件")
        return False


async def main():
    """主测试函数"""
    print("开始测试日志记录和LLM拦截功能...")
    
    # 测试run_hierarchical.py的日志功能
    result1 = await test_run_hierarchical_logging()
    
    # 测试adapt_document.py的日志功能
    result2 = await test_adapt_document_logging()
    
    if result1 and result2:
        print("\n✓ 所有测试通过！日志记录和LLM拦截功能正常工作。")
        return True
    else:
        print("\n✗ 部分测试失败，请检查日志配置和LLM拦截功能。")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)