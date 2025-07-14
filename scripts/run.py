# /root/metagpt/mgfr/scripts/run.py

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
from metagpt.context import Context
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.actions.add_requirement import UserRequirement as OrigUserRequirement

# 导入角色和Schema
from metagpt_doc_writer.roles import ChiefPM, Executor, Archiver
from metagpt_doc_writer.schemas.doc_structures import Plan, Task, FinalDelivery, UserRequirement
from metagpt_doc_writer.mcp.manager import MCPManager

# --- 全局常量 ---
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
logger.add(LOGS_DIR / "run.log", rotation="10 MB", retention="1 week", level="INFO")
OUTPUT_PATH = PROJECT_ROOT / "outputs"
OUTPUT_PATH.mkdir(exist_ok=True)
ARCHIVE_PATH = PROJECT_ROOT / "archive"
ARCHIVE_PATH.mkdir(exist_ok=True)

async def main(idea: str, investment: float = 100.0):
    """主异步函数，作为确定性的主调度循环，并正确管理共享资源。"""
    logger.info(f"Starting document generation process for: '{idea}'")

    # --- 1. 配置加载 ---
    config_yaml_path = Path(os.environ.get("METAGPT_CONFIG_PATH", Path.home() / ".metagpt/config2.yaml"))
    if not config_yaml_path.exists():
        config_yaml_path = PROJECT_ROOT / "configs" / "config2.yaml"
    if not config_yaml_path.exists():
        raise FileNotFoundError(f"Configuration file (config2.yaml) not found at: {config_yaml_path}")
    
    with open(config_yaml_path, 'r', encoding='utf-8') as f:
        full_config = yaml.safe_load(f)

    # --- 2. 创建独立的共享资源 (Context 和 MCPManager) ---
    config = Config.from_yaml_file(config_yaml_path)
    if hasattr(config, 'human_in_loop'):
        config.human_in_loop = False
    
    ctx = Context(config=config)
    
    mcp_server_configs = full_config.get("mcp_servers", {})
    mcp_manager = MCPManager(server_configs=mcp_server_configs)
    await mcp_manager.start_servers()
    
    logger.info("Shared Context and MCP Manager created successfully.")

    # --- 3. 初始化角色，并通过构造函数注入依赖 ---
    mcp_bindings = full_config.get("role_mcp_bindings", {})
    
    chief_pm = ChiefPM(context=ctx, mcp_manager=mcp_manager, mcp_bindings=mcp_bindings)
    executor = Executor(context=ctx, mcp_manager=mcp_manager, mcp_bindings=mcp_bindings)
    archiver = Archiver(context=ctx, archive_path=str(ARCHIVE_PATH))
    
    logger.info("Core roles (ChiefPM, Executor, Archiver) initialized with dependencies.")

    # =======================================================================
    #  手动串行调度循环 (代替 team.run())
    # =======================================================================
    
    # 步骤 1: ChiefPM 制定计划
    logger.info("--- Phase 1: Planning ---")
    user_req_msg = Message(content=idea, instruct_content=UserRequirement(content=idea), cause_by=OrigUserRequirement)
    plan_msg = await chief_pm.run(user_req_msg)
    if not plan_msg or not isinstance(plan_msg.instruct_content, Plan):
        logger.error("ChiefPM failed to generate a valid plan. Aborting.")
        await mcp_manager.close()
        return
        
    plan: Plan = plan_msg.instruct_content
    logger.success(f"Plan generated with {len(plan.tasks)} tasks.")

    # 步骤 2: 串行执行任务
    logger.info("--- Phase 2: Execution ---")
    completed_tasks: dict[str, Task] = {}
    
    while len(completed_tasks) < len(plan.tasks):
        ready_tasks = plan.get_ready_tasks(list(completed_tasks.keys()))
        
        if not ready_tasks:
            if len(completed_tasks) < len(plan.tasks):
                logger.warning("Execution loop finished, but not all tasks are complete. Possible dependency cycle.")
            break
            
        current_task = plan.task_map[ready_tasks[0].task_id]
        
        logger.info(f"Executing task '{current_task.task_id}': {current_task.instruction}")
        
        # Executor现在直接接收Task和完整的已完成任务字典
        updated_task = await executor.run(current_task, completed_tasks)
        completed_tasks[updated_task.task_id] = updated_task
        
        logger.success(f"Task '{updated_task.task_id}' completed.")

    logger.info("--- All tasks executed. ---")

    # 步骤 3: 结果处理与归档
    logger.info("--- Phase 3: Finalizing ---")
    final_doc_content = f"# PRD: {idea}\n\n---\n"
    for task_id in sorted(plan.task_map.keys()):
        task = completed_tasks.get(task_id)
        if task:
            final_doc_content += f"## ✅ Task: {task.instruction}\n**Action Type**: `{task.action_type}`\n**Result**:\n\n{task.result}\n\n---\n"
        else:
            final_doc_content += f"## ❌ Task: {plan.task_map[task_id].instruction}\n**Result**: Skipped or Failed\n\n---\n"
    
    safe_idea = "".join(c for c in idea if c.isalnum() or c in " _-").rstrip()
    final_doc_path = OUTPUT_PATH / f"prd_{safe_idea[:50]}.md"
    final_doc_path.write_text(final_doc_content, encoding='utf-8')
    logger.success(f"Final document generated at: {final_doc_path}")

    await archiver.archive(final_doc_path=str(final_doc_path), all_tasks=completed_tasks, plan=plan)

    # --- 步骤 4: 清理与关闭 ---
    await mcp_manager.close()
    logger.info("MCP Manager connections closed.")

if __name__ == "__main__":
    idea_from_args = " ".join(sys.argv[1:])
    if not idea_from_args:
        idea_from_args = "Write a detailed technical guide on how to install autogen and implement a concurrent multi-expert discussion using its GroupChat feature."
    
    try:
        asyncio.run(main(idea=idea_from_args))
    except Exception as e:
        logger.error(f"An unexpected error occurred in the main run: {e}", exc_info=True)