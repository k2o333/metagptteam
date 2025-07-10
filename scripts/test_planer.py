# 路径: /root/metagpt/mgfr/scripts/test_planner.py (新增文件全文)
import sys
import os
import asyncio
from pathlib import Path

# 设置项目根目录以便正确导入模块
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from metagpt.config2 import Config
from metagpt.provider.openai_api import OpenAILLM
from metagpt_doc_writer.actions.create_plan import CreatePlan

async def main():
    # 手动加载配置，确保使用正确的LLM
    config = Config.default()
    if config.llm:
        config.llm.api_type = "open_llm" # 强制使用 open_llm
        llm = OpenAILLM(config=config.llm)
    else:
        print("LLM configuration not found. Please check your config file.")
        return

    # 实例化我们的Action
    create_plan_action = CreatePlan()
    create_plan_action.set_llm(llm) # 为Action设置LLM实例

    # 定义一个测试目标
    test_goal = "写一个给定技术文档，能出代码的，metagpt的多智能体脚本的prd"
    
    print(f"Testing planner with goal: '{test_goal}'")
    print("="*30)

    # 运行Action并捕获可能的错误
    try:
        await create_plan_action.run(goal=test_goal)
    except Exception as e:
        print(f"\n🚨 An error occurred during the test run: {e}")

if __name__ == "__main__":
    asyncio.run(main())