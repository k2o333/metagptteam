# /root/metagpt/mgfr/scripts/run.py (修正版)

import sys
import asyncio
from pathlib import Path
import yaml
import os
import json

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# --- MetaGPT 和自定义模块导入 ---
from metagpt.config2 import Config
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.actions.add_requirement import UserRequirement

# 导入角色和Schema
from metagpt_doc_writer.roles import ChiefPM, Executor
from metagpt_doc_writer.schemas.doc_structures import Plan, Task, FinalDelivery

# --- 全局常量 (保持不变) ---
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
logger.add(LOGS_DIR / "run.log", rotation="10 MB", retention="1 week", level="INFO")
OUTPUT_PATH = PROJECT_ROOT / "outputs"
OUTPUT_PATH.mkdir(exist_ok=True)
ARCHIVE_PATH = PROJECT_ROOT / "archive"
ARCHIVE_PATH.mkdir(exist_ok=True)

async def main(idea: str, investment: float = 100.0, max_tasks: int = 10):
    """主异步函数，作为确定性的主调度循环。"""
    logger.info(f"Starting document generation process for: '{idea}'")

    # --- 配置加载 (保持不变) ---
    config_yaml_path = Path(os.environ.get("METAGPT_CONFIG_PATH", Path.home() / ".metagpt/config2.yaml"))
    if not config_yaml_path.exists():
        config_yaml_path = PROJECT_ROOT / "configs" / "config2.yaml"
    os.environ["METAGPT_CONFIG_PATH"] = str(config_yaml_path)
    config = Config.default()
    if hasattr(config, 'human_in_loop'):
        config.human_in_loop = False

    # --- 初始化核心角色 ---
    chief_pm = ChiefPM()
    executor = Executor()
    logger.info("Core roles (ChiefPM, Executor) initialized.")

    # =======================================================================
    #  手动串行调度循环
    # =======================================================================
    
    # 步骤 1: ChiefPM 制定计划
    logger.info("--- Phase 1: Planning ---")
    # 修正：直接使用标准Message，不再需要CustomUserRequirement
    user_req_msg = Message(content=idea, cause_by=UserRequirement)
    plan_msg = await chief_pm.run(user_req_msg)
    if not plan_msg or not isinstance(plan_msg.instruct_content, Plan):
        logger.error("ChiefPM failed to generate a valid plan. Aborting.")
        return
        
    plan: Plan = plan_msg.instruct_content
    logger.success(f"Plan generated with {len(plan.tasks)} tasks.")

    # 步骤 2: 串行执行任务
    logger.info("--- Phase 2: Execution ---")
    completed_tasks = set()
    task_results = {}
    
    while len(completed_tasks) < len(plan.tasks):
        ready_tasks = plan.get_ready_tasks(completed_tasks)
        
        if not ready_tasks:
            logger.warning("No more ready tasks, but plan is not complete. There might be a dependency cycle.")
            break
            
        current_task = ready_tasks[0]
        
        logger.info(f"Executing task '{current_task.task_id}': {current_task.instruction}")
        
        context_str = "\n---\n".join([
            f"### Result from dependent task '{dep_id}':\n{task_results.get(dep_id, '')}"
            for dep_id in current_task.dependent_task_ids
        ])
        current_task.context['dependency_results'] = context_str

        task_msg = Message(content=current_task.instruction, instruct_content=current_task)
        result_msg = await executor.run(task_msg)

        task_results[current_task.task_id] = result_msg.content
        completed_tasks.add(current_task.task_id)
        
        logger.success(f"Task '{current_task.task_id}' completed.")

    logger.info("--- All tasks executed. ---")

    # 步骤 3: 结果处理
    logger.info("--- Phase 3: Finalizing ---")
    # ... (这部分逻辑保持不变) ...
    final_doc_content = "# Final Document\n\n"
    for task in plan.tasks:
        result = task_results.get(task.task_id, "Execution failed or skipped.")
        final_doc_content += f"## ✅ Task: {task.instruction}\n**Result**:\n\n{result}\n\n---\n\n"
    
    final_doc_path = OUTPUT_PATH / f"prd_{idea.replace(' ', '_')[:30]}.md"
    final_doc_path.write_text(final_doc_content, encoding='utf-8')
    logger.success(f"Final document generated at: {final_doc_path}")


if __name__ == "__main__":
    idea_from_args = " ".join(sys.argv[1:])
    if not idea_from_args:
        idea_from_args = "Write a detailed technical guide on how to install autogen and implement a concurrent multi-expert discussion using its GroupChat feature."
    
    try:
        asyncio.run(main(idea=idea_from_args))
    except Exception as e:
        logger.error(f"An unexpected error occurred in the main run: {e}", exc_info=True)