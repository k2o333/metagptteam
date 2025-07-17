# /root/metagpt/mgfr/scripts/run.py

import sys
import asyncio
from pathlib import Path
import yaml
import os
import json

from metagpt.config2 import Config
from metagpt.context import Context
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.provider.llm_provider_registry import create_llm_instance
from metagpt.configs.models_config import ModelsConfig

from metagpt_doc_writer.roles import ChiefPM, Executor, Archiver
from metagpt_doc_writer.schemas.doc_structures import Plan, Task
from metagpt_doc_writer.actions.finalize import FinalizeDocument

# --- 全局常量 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
logger.add(LOGS_DIR / "run.log", rotation="10 MB", retention="1 week", level="INFO")
OUTPUT_PATH = PROJECT_ROOT / "outputs"
OUTPUT_PATH.mkdir(exist_ok=True)
ARCHIVE_PATH = PROJECT_ROOT / "archive"
ARCHIVE_PATH.mkdir(exist_ok=True)

async def main(idea: str):
    """主异步函数，采用完全的外部手动调度，并遵循所有官方最佳实践。"""
    logger.info(f"Starting document generation process for: '{idea}'")

    # --- 1. 配置与Context ---
    config_yaml_path = Path(os.environ.get("METAGPT_CONFIG_PATH", Path.home() / ".metagpt/config2.yaml"))
    if not config_yaml_path.exists():
        config_yaml_path = PROJECT_ROOT / "configs" / "config2.yaml"
    if not config_yaml_path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {config_yaml_path}")
    
    config = Config.from_yaml_file(config_yaml_path)
    ctx = Context(config=config)
    
    assert ctx.config.llm is not None, "Default LLM config is missing."

    # --- 2. 初始化角色 ---
    logger.info("Initializing roles as standalone services...")
    chief_pm = ChiefPM(context=ctx)
    executor = Executor(context=ctx)
    archiver = Archiver(context=ctx, archive_path=str(ARCHIVE_PATH))
    logger.info("Core roles initialized.")

    # --- 3. 调度循环 ---
    # 阶段1: 规划
    logger.info("--- Phase 1: Planning ---")
    plan_msg = await chief_pm.run(Message(content=idea))
    plan: Plan = plan_msg.instruct_content
    logger.success(f"Plan generated with {len(plan.tasks)} tasks.")

    # 阶段2: 执行
    logger.info("--- Phase 2: Execution ---")
    completed_tasks: dict[str, Task] = {}
    document_snippets: dict[str, str] = {}

    while len(completed_tasks) < len(plan.tasks):
        ready_tasks = plan.get_ready_tasks(list(completed_tasks.keys()))
        if not ready_tasks:
            if len(completed_tasks) < len(plan.tasks):
                logger.warning("Execution loop finished, but not all tasks are complete.")
            break
            
        current_task = plan.task_map[ready_tasks[0].task_id]
        
        logger.info(f"Executing task '{current_task.task_id}': {current_task.instruction}")
        
        try:
            updated_task = await executor.run(current_task, completed_tasks, document_snippets)
            completed_tasks[updated_task.task_id] = updated_task
            if updated_task.target_snippet_id:
                document_snippets[updated_task.target_snippet_id] = updated_task.result
            logger.success(f"Task '{updated_task.task_id}' completed.")
        except Exception as e:
            logger.error(f"Task '{current_task.task_id}' failed with a critical error: {e}", exc_info=True)
            failed_task = current_task
            failed_task.result = f"CRITICAL EXECUTION FAILED: {e}"
            completed_tasks[failed_task.task_id] = failed_task
            break

    logger.info("--- All tasks executed. ---")

    # 阶段3: 整合与定稿
    logger.info("--- Phase 3: Finalization ---")
    
    # 【核心修正】: 为FinalizeDocument创建一个拥有正确LLM配置的专用Context
    models_config = ModelsConfig.default()
    strong_llm_key = "gpt_4o_strong"
    strong_llm_config = models_config.get(strong_llm_key)
    
    if strong_llm_config:
        # 创建一个新配置对象，只覆盖llm部分
        finalize_config = config.model_copy(deep=True)
        finalize_config.llm = strong_llm_config
        finalize_ctx = Context(config=finalize_config)
        logger.info(f"Using strong model '{strong_llm_key}' for finalization.")
    else:
        # 如果找不到强模型配置，就使用默认的Context
        finalize_ctx = ctx
        logger.warning(f"Strong model key '{strong_llm_key}' not found in config.models, using default LLM for finalization.")
    
    # 创建Action实例时，传入这个专用的Context
    finalize_action = FinalizeDocument(context=finalize_ctx)
    
    # 现在Action会从其自己的context中正确获取LLM，无需手动set_llm
    pure_document_content = await finalize_action.run(plan=plan, snippets=document_snippets)
    
    safe_idea = "".join(c for c in idea if c.isalnum() or c in " _-").rstrip()
    final_doc_path = OUTPUT_PATH / f"final_doc_{safe_idea[:50]}.md"
    final_doc_path.write_text(pure_document_content, encoding='utf-8')
    logger.success(f"Final, clean document generated at: {final_doc_path}")

    # 阶段4: 归档
    await archiver.archive(
        final_doc_path=str(final_doc_path), 
        all_tasks=completed_tasks,
        plan=plan
    )

if __name__ == "__main__":
    idea_from_args = " ".join(sys.argv[1:])
    if not idea_from_args:
        idea_from_args = "metagpt最新版本的_plan_and_act模式是什么"
    
    try:
        asyncio.run(main(idea=idea_from_args))
    except Exception as e:
        logger.error(f"An unexpected error occurred in the main run: {e}", exc_info=True)