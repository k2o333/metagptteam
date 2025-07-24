# scripts/run_hierarchical.py
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
from hierarchical.schemas import Outline

# --- 导入所有角色 ---
from hierarchical.roles.chief_pm import ChiefPM
from hierarchical.roles.scheduler import Scheduler
from hierarchical.roles.executor import Executor
from hierarchical.roles.archiver import Archiver

# --- 日志设置 ---
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
logger.remove()
logger.add(sys.stderr, level="DEBUG")
logger.add(LOGS_DIR / "run_hierarchical.log", rotation="10 MB", retention="1 week", level="DEBUG")

async def main(idea: str, n_round: int = 500):
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

    global_config = Config.from_yaml_file(global_config_path)
    
    raw_global_config_data: Dict[str, Any] = {}
    with open(global_config_path, 'r', encoding='utf-8') as f:
        raw_global_config_data = yaml.safe_load(f) or {}
    
    local_config_data: Dict[str, Any] = {}
    if local_config_path.is_file():
        logger.info(f"正在从 {local_config_path} 加载本地项目配置...")
        with open(local_config_path, 'r', encoding='utf-8') as f:
            local_config_data = yaml.safe_load(f) or {}
    else:
        logger.warning(f"本地项目配置文件未找到: {local_config_path}. 将使用默认策略。")

    # --- 2. 上下文 (Context) 初始化 ---
    ctx = HierarchicalContext(config=global_config)
    ctx.kwargs.custom_config = {**raw_global_config_data, **local_config_data}
    ctx.kwargs.strategy_config = local_config_data
    hierarchical_config = ctx.kwargs.custom_config.get("hierarchical_doc_writer", {})
    semaphore_limit = hierarchical_config.get("strong_model_semaphore_limit", 2)
    ctx.semaphore = asyncio.Semaphore(semaphore_limit)
    ctx.outline = Outline(goal=idea)
    
    logger.info(f"上下文初始化完成。信号量限制: {semaphore_limit}")

    # --- 3. 团队组建 ---
    team = Team(context=ctx, use_mgx=False)
    team.hire([ChiefPM(), Scheduler(), Executor(), Archiver()])

    # --- 4. 运行 (带强制归档) ---
    try:
        logger.info(f"使用 team.run(idea=...) 启动项目，最大轮次: {n_round}")
        await team.run(idea=idea, n_round=n_round) 
    except Exception as e:
        logger.error(f"团队运行期间发生异常: {e}", exc_info=True)
    finally:
        logger.info("--- 强制执行最终归档（无论成功与否） ---")
        archiver = team.env.get_role("Archiver")
        if archiver and hasattr(archiver, '_assemble_document'):
            outline: Outline = archiver.context.outline
            if outline and (outline.root_sections or outline.goal):
                final_doc_content = archiver._assemble_document(outline)

                output_path = Path("outputs") 
                output_path.mkdir(exist_ok=True)
                
                timestamp = "final_forced"
                safe_goal_name = "".join(c for c in outline.goal if c.isalnum() or c in " _-").strip()[:50]
                doc_filename = f"final_document_{safe_goal_name}_{timestamp}.md"
                doc_path = output_path / doc_filename
                doc_path.write_text(final_doc_content, encoding='utf-8')
                
                logger.success(f"强制归档成功！最终（或半成品）文档已生成: {doc_path}")
            else:
                logger.warning("无法进行强制归档，因为outline为空或没有内容。")

    # --- 5. 结束 ---
    logger.info("--- 团队运行结束 ---")
    print(f"\n--- 文档生成流程完成，请检查 'outputs' 目录 ---")

if __name__ == "__main__":
    user_idea = "人工智能在教育领域的应用"
    asyncio.run(main(idea=user_idea))