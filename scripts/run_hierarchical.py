# scripts/run_hierarchical.py
import asyncio
import sys
from pathlib import Path
import yaml
from typing import List

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

# --- 导入新的Roles，包括 Archiver ---
from hierarchical.roles.chief_pm import ChiefPM
from hierarchical.roles.scheduler import Scheduler
from hierarchical.roles.executor import Executor
from hierarchical.roles.archiver import Archiver # <-- 【核心新增】导入 Archiver

LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
logger.add(LOGS_DIR / "run_hierarchical.log", rotation="10 MB", retention="1 week")

def assemble_final_document(outline: Outline) -> str:
    """
    Recursively assembles the final document from the outline,
    adding markdown headings based on section level.
    This function is now only used for initial placeholder/testing.
    The real assembly happens in Archiver.
    """
    if not outline:
        return "# Error: Outline object was not found or is empty."
        
    content_parts = []
    
    def recurse_assemble(sections: List[Section]):
        sorted_sections = sorted(sections, key=lambda s: s.display_id)
        for section in sorted_sections:
            title_prefix = '#' * section.level
            content_parts.append(f"{title_prefix} {section.display_id} {section.title}")
            if section.content:
                content_parts.append(section.content)
            if section.sub_sections:
                recurse_assemble(section.sub_sections)

    content_parts.append(f"# {outline.goal}")
    recurse_assemble(outline.root_sections)
    return "\n\n".join(content_parts)

async def main(idea: str):
    logger.info(f"--- 启动新架构文档生成任务 ---")
    logger.info(f"目标: {idea}")

    config_path = Path("/root/.metagpt/config2.yaml")
    if not config_path.is_file():
        logger.error(f"配置文件未找到: {config_path}")
        return

    logger.info(f"正在从 {config_path} 加载配置...")
    config = Config.from_yaml_file(config_path)
    ctx = HierarchicalContext(config=config)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        custom_config = yaml.safe_load(f)
    if custom_config:
        ctx.kwargs.custom_config = custom_config
    
    hierarchical_config = custom_config.get("hierarchical_doc_writer", {}) if custom_config else {}
    semaphore_limit = hierarchical_config.get("strong_model_semaphore_limit", 2)
    ctx.semaphore = asyncio.Semaphore(semaphore_limit)
    ctx.outline = Outline(goal=idea)

    team = Team(context=ctx, use_mgx=False)
    team.hire([
        ChiefPM(),
        Scheduler(),
        Executor(),
        Archiver() # <-- 【核心新增】雇佣 Archiver 角色
    ])

    logger.info("使用 team.run(idea=...) 启动项目...")
    await team.run(idea=idea, n_round=50) # 增加轮次以支持更深的文档

    # --- 【核心移除】所有流程结束后的手动文档处理逻辑 ---
    logger.info("--- 团队运行结束 ---")
    print(f"\n--- 文档生成流程完成，请检查 'outputs' 目录 ---")


if __name__ == "__main__":
    user_idea = "人工智能在教育领域的应用"
    asyncio.run(main(idea=user_idea))