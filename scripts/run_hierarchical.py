# scripts/run_hierarchical.py
import asyncio
import sys
from pathlib import Path
import yaml

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
# --- 导入我们自定义的Context和核心Schema ---
from hierarchical.context import HierarchicalContext
from hierarchical.schemas import Outline

# --- 导入新的Roles ---
from hierarchical.roles.chief_pm import ChiefPM
from hierarchical.roles.scheduler import Scheduler
from hierarchical.roles.executor import Executor

LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
logger.add(LOGS_DIR / "run_hierarchical.log", rotation="10 MB", retention="1 week")

def assemble_final_document(outline: Outline) -> str:
    """Recursively assembles the final document from the outline."""
    if not outline:
        return "# Error: Outline object was not found or is empty."
        
    content_parts = []
    
    def recurse_assemble(sections, current_level):
        sorted_sections = sorted(sections, key=lambda s: s.display_id)
        for section in sorted_sections:
            content_parts.append(section.content)
            if section.sub_sections:
                recurse_assemble(section.sub_sections, current_level + 1)

    content_parts.append(f"# {outline.goal}")
    recurse_assemble(outline.root_sections, 1)
    return "\n\n".join(content_parts)

async def main(idea: str):
    logger.info(f"--- 启动新架构文档生成任务 ---")
    logger.info(f"目标: {idea}")

    # 1. 加载配置
    config_path = Path("/root/.metagpt/config2.yaml")
    if not config_path.is_file():
        logger.error(f"配置文件未找到或不是一个文件，请检查路径: {config_path}")
        return

    logger.info(f"正在从 {config_path} 加载配置...")
    config = Config.from_yaml_file(config_path)
    ctx = HierarchicalContext(config=config)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        custom_config = yaml.safe_load(f)
    if custom_config:
        ctx.kwargs.custom_config = custom_config
    
    # 2. 创建并存储不可序列化的对象
    hierarchical_config = custom_config.get("hierarchical_doc_writer", {}) if custom_config else {}
    semaphore_limit = hierarchical_config.get("strong_model_semaphore_limit", 2)
    ctx.semaphore = asyncio.Semaphore(semaphore_limit)
    ctx.outline = Outline(goal=idea)

    # 3. 初始化Team
    team = Team(context=ctx, use_mgx=False)
    team.hire([
        ChiefPM(),
        Scheduler(),
        Executor()
    ])

    # 4. 启动项目和执行循环
    logger.info("使用 team.run(idea=...) 启动项目...")
    # 增加轮次，给角色们足够的时间来回传递消息
    await team.run(idea=idea, n_round=10)

    # 5. 结束后，组装并保存最终文档
    logger.info("--- 流程结束，正在组装最终文档 ---")
    final_outline = ctx.outline
    final_doc_content = assemble_final_document(final_outline)
    
    output_path = PROJECT_ROOT / "outputs"
    output_path.mkdir(exist_ok=True)
    doc_path = output_path / "final_document.md"
    doc_path.write_text(final_doc_content, encoding='utf-8')
    
    logger.success(f"最终文档已生成: {doc_path}")
    print(f"\n最终文档内容预览:\n---\n{final_doc_content}\n---")


if __name__ == "__main__":
    user_idea = "人工智能在教育领域的应用"
    asyncio.run(main(idea=user_idea))