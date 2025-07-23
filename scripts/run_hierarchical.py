# scripts/run_hierarchical.py (最终整合版)
import asyncio
import sys
from pathlib import Path
import yaml
from typing import List, Dict, Any

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# -----------------

from metagpt.config2 import Config
from metagpt.logs import logger
from metagpt.team import Team
from metagpt.schema import Message
from hierarchical.context import HierarchicalContext
from hierarchical.schemas import Outline, Section

# --- 导入所有角色 ---
from hierarchical.roles.chief_pm import ChiefPM
from hierarchical.roles.scheduler import Scheduler
from hierarchical.roles.executor import Executor
from hierarchical.roles.archiver import Archiver

# --- 日志设置 ---
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
logger.add(LOGS_DIR / "run_hierarchical.log", rotation="10 MB", retention="1 week")

async def main(idea: str, n_round: int = 50):
    """
    主运行函数，负责设置、组建团队并运行。
    """
    logger.info(f"--- 启动新架构文档生成任务 ---")
    logger.info(f"目标: {idea}")

    # --- 1. 配置加载 ---
    global_config_path = Path("/root/.metagpt/config2.yaml")
    local_config_path = PROJECT_ROOT / "configs" / "local_config.yaml"

    if not global_config_path.is_file():
        logger.error(f"全局配置文件未找到: {global_config_path}")
        return

    # 加载 MetaGPT 标准配置 (llm, embedding, models, etc.)
    logger.info(f"正在从 {global_config_path} 加载全局配置...")
    global_config = Config.from_yaml_file(global_config_path)

    # 读取原始全局YAML以提取我们自定义的顶层配置 (如 private_rag_service)
    raw_global_config_data: Dict[str, Any] = {}
    with open(global_config_path, 'r', encoding='utf-8') as f:
        raw_global_config_data = yaml.safe_load(f) or {}
    
    # 加载本地项目级策略配置
    local_config_data: Dict[str, Any] = {}
    if local_config_path.is_file():
        logger.info(f"正在从 {local_config_path} 加载本地项目配置...")
        with open(local_config_path, 'r', encoding='utf-8') as f:
            local_config_data = yaml.safe_load(f) or {}
    else:
        logger.warning(f"本地项目配置文件未找到: {local_config_path}. 将使用默认策略。")

    # --- 2. 上下文 (Context) 初始化 ---
    ctx = HierarchicalContext(config=global_config)

    # 将所有自定义配置（全局自定义 + 本地策略）统一放入 context.kwargs.custom_config
    # 这样，任何角色都可以通过 self.context.kwargs.custom_config 访问到所有非标准配置
    ctx.kwargs.custom_config = {
        **raw_global_config_data, # 包含 private_rag_service 等
        **local_config_data,      # 包含 role_pools, hierarchical_doc_writer 等
    }
    
    # 为了向后兼容和代码清晰，也可以单独设置策略配置
    ctx.kwargs.strategy_config = local_config_data

    # 从合并后的自定义配置中获取 hierarchical_doc_writer 设置
    hierarchical_config = ctx.kwargs.custom_config.get("hierarchical_doc_writer", {})
    semaphore_limit = hierarchical_config.get("strong_model_semaphore_limit", 2)
    
    # 设置关键的运行时对象
    ctx.semaphore = asyncio.Semaphore(semaphore_limit)
    ctx.outline = Outline(goal=idea)
    
    logger.info(f"上下文初始化完成。信号量限制: {semaphore_limit}")

    # --- 3. 团队组建 ---
    team = Team(context=ctx, use_mgx=False)
    team.hire([
        ChiefPM(),
        Scheduler(),
        Executor(),
        Archiver()
    ])

    # --- 4. 运行 ---
    logger.info(f"使用 team.run(idea=...) 启动项目，最大轮次: {n_round}")
    await team.run(idea=idea, n_round=n_round) 

    # --- 5. 结束 ---
    logger.info("--- 团队运行结束 ---")
    print(f"\n--- 文档生成流程完成，请检查 'outputs' 目录 ---")


if __name__ == "__main__":
    user_idea = "人工智能在教育领域的应用"
    # 确保私有RAG服务正在另一个终端中运行
    # uvicorn main:app --host 0.0.0.0 --port 9000
    asyncio.run(main(idea=user_idea))