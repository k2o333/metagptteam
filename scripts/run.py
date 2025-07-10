# 路径: /root/metagpt/mgfr/scripts/run.py (修复并优化的版本)

import sys
import asyncio
from pathlib import Path

# --- 路径设置，确保自定义模块能被正确导入 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from metagpt.config2 import Config
from metagpt.logs import logger
from metagpt.provider.openai_api import OpenAILLM
from metagpt.roles import Role  # 引入Role基类，用于类型提示

# --- 导入你的自定义组件 ---
try:
    from metagpt_doc_writer.roles.planner import Planner
    from metagpt_doc_writer.actions.research import Research
    from metagpt_doc_writer.actions.write import Write
    from metagpt_doc_writer.actions.review import Review
    from metagpt_doc_writer.schemas.doc_structures import Plan
    from scripts.team_scheduler import Scheduler # 引入我们新的、更可靠的调度器
except ImportError as e:
    logger.error(f"导入自定义组件失败，请检查文件路径和名称。错误: {e}")
    sys.exit(1)


# --- 日志和输出路径设置 ---
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
logger.add(LOGS_DIR / "run.log", rotation="10 MB", retention="1 week", level="INFO")

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)


async def start_app(idea: str, investment: float = 20.0, n_round: int = 40):
    """
    使用显式编排的流水线模式启动文档生成流程。
    """
    # --- 1. 配置加载和LLM初始化 ---
    logger.info("正在加载配置...")
    config = Config.default()
    if not config.llm or not getattr(config.llm, 'api_key', None):
        logger.error("LLM配置不完整，请检查 ~/.metagpt/config2.yaml 或项目内的 configs/config2.yaml 文件。")
        return
        
    # 强制使用 open_llm 类型以支持通过 base_url 连接的任何兼容OpenAI的API
    config.llm.api_type = "open_llm" 
    llm_instance = OpenAILLM(config=config.llm)
    logger.info(f"LLM实例创建成功，模型: '{llm_instance.model}'")

    # ==========================================================
    # Phase 1: 规划阶段 (Planning Phase)
    # ==========================================================
    logger.info("--- 规划阶段开始 ---")
    planner = Planner(llm=llm_instance)
    
    # 运行Planner来获取计划。这里我们直接调用其run方法，而不是通过Team。
    # 这是一个更直接、更可靠的获取计划的方式。
    plan: Plan = await planner.actions[0].run(goal=idea)
    if not plan or not plan.tasks:
        logger.error("规划失败，未能生成有效计划。流程终止。")
        return
    logger.info(f"✅ 规划成功，生成了 {len(plan.tasks)} 个任务。")
    logger.debug(f"生成的计划详情:\n{plan.model_dump_json(indent=2)}")

    # ==========================================================
    # Phase 2: 执行阶段 (Execution Phase)
    # ==========================================================
    logger.info("--- 执行阶段开始 ---")
    
    # 1. 定义所有可执行的角色和他们能执行的Action
    # 这里的'Executor'是一个概念，你可以有多个不同技能的'Executor'
    # 我们用一个字典来管理他们，key是Action的类型
    executor_role = Role() # 创建一个通用的Role来承载actions
    executor_role.set_llm(llm_instance)
    executor_role.set_actions([Research(), Write(), Review()])
    
    # 2. 创建并运行调度器
    # 调度器接收计划和所有可执行角色
    scheduler = Scheduler(plan=plan, roles={"RESEARCH": executor_role, "WRITE": executor_role, "REVIEW": executor_role})
    await scheduler.run()
    
    task_results = scheduler.task_results

    # ==========================================================
    # 4. 结果整合与输出 (Result Integration)
    # ==========================================================
    logger.info("--- 结果整合阶段开始 ---")
    
    if len(task_results) != len(plan.tasks):
        logger.warning("部分任务未能完成。报告中将注明未完成的任务。")

    final_content = [f"# PRD: {idea}\n\n---\n"]
    
    for task in plan.tasks:
        if task.task_id in task_results:
            result = task_results[task.task_id]
            final_content.append(f"## ✅ Task: {task.instruction}\n")
            final_content.append(f"**Action Type**: `{task.action_type}`\n")
            final_content.append(f"**Result**:\n\n{result}\n\n---\n")
        else:
            final_content.append(f"## ❌ Task: {task.instruction}\n")
            final_content.append("**This task was not completed.**\n\n---\n")
    
    sanitized_idea = "".join(c if c.isalnum() else "_" for c in idea)[:50]
    output_path = OUTPUTS_DIR / f"prd_{sanitized_idea}.md"
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("".join(final_content))
        logger.info(f"🎉 最终文档已成功生成！请查看: {output_path}")
    except Exception as e:
        logger.error(f"写入最终文件失败: {e}")

    logger.info("文档生成流程全部完成！")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_idea = " ".join(sys.argv[1:])
    else:
        user_idea = "写一个给定技术文档，能出代码的，metagpt的多智能体脚本的prd"
    
    try:
        asyncio.run(start_app(idea=user_idea))
    except Exception as e:
        logger.error(f"主程序发生未捕获的异常并终止: {e}", exc_info=True)