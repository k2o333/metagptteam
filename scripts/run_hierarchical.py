# scripts/run_hierarchical.py (The Definitive Final Version)
import asyncio
import sys
from pathlib import Path
import yaml
from typing import List, Dict, Any, Optional, Union

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
from metagpt.provider.base_llm import BaseLLM
from metagpt.const import USE_CONFIG_TIMEOUT # 【核心新增】
from hierarchical.context import HierarchicalContext
from hierarchical.schemas import Outline
from hierarchical.roles import ChiefPM, Scheduler, Executor, Archiver

# --- 日志设置 ---
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
logger.remove()
logger.add(sys.stderr, level="DEBUG")
logger.add(LOGS_DIR / "run_hierarchical.log", rotation="10 MB", retention="1 week", level="DEBUG")

# --- 【核心修正】: 使用正确的 aask 函数签名进行猴子补丁 ---
def patch_llm_aask(context: HierarchicalContext):
    """
    通过猴子补丁，在每次成功的 aask 调用后增加 context.kwargs 中的计数器。
    """
    original_aask = BaseLLM.aask

    async def patched_aask(
        self: BaseLLM,
        msg: Union[str, List[Dict[str, str]]],
        system_msgs: Optional[List[str]] = None,
        format_msgs: Optional[List[Dict[str, str]]] = None,
        images: Optional[Union[str, List[str]]] = None,
        timeout=USE_CONFIG_TIMEOUT,
        stream=None,
    ) -> str:
        # 调用原始的 aask 方法，并传递所有参数
        result = await original_aask(self, msg=msg, system_msgs=system_msgs, format_msgs=format_msgs, images=images, timeout=timeout, stream=stream)
        
        if 'successful_llm_calls' in context.kwargs:
            context.kwargs.successful_llm_calls += 1
            logger.debug(f"LLM call successful. Total count: {context.kwargs.successful_llm_calls}")
        
        return result

    if not getattr(BaseLLM.aask, '_is_patched', False):
        BaseLLM.aask = patched_aask
        setattr(BaseLLM.aask, '_is_patched', True)
        logger.info("BaseLLM.aask has been patched to count successful calls.")


async def main(idea: str, max_llm_calls: int = 59):
    """
    主运行函数，使用自定义的、基于LLM调用次数的运行循环。
    """
    logger.info(f"--- 启动新架构文档生成任务 ---")
    logger.info(f"目标: {idea}")
    logger.info(f"运行将在 {max_llm_calls} 次成功的LLM调用后终止。")

    # --- 1. 配置加载 ---
    global_config_path = Path("/root/.metagpt/config2.yaml")
    local_config_path = PROJECT_ROOT / "configs" / "local_config.yaml"
    
    global_config = Config.from_yaml_file(global_config_path)
    
    raw_global_config_data: Dict[str, Any] = {}
    with open(global_config_path, 'r', encoding='utf-8') as f:
        raw_global_config_data = yaml.safe_load(f) or {}
    
    local_config_data: Dict[str, Any] = {}
    if local_config_path.is_file():
        with open(local_config_path, 'r', encoding='utf-8') as f:
            local_config_data = yaml.safe_load(f) or {}

    # --- 2. 上下文 (Context) 初始化 ---
    ctx = HierarchicalContext(config=global_config)
    ctx.kwargs.custom_config = {**raw_global_config_data, **local_config_data}
    ctx.kwargs.strategy_config = local_config_data
    ctx.kwargs.successful_llm_calls = 0
    
    hierarchical_config = ctx.kwargs.custom_config.get("hierarchical_doc_writer", {})
    semaphore_limit = hierarchical_config.get("strong_model_semaphore_limit", 3) # 增加信号量以提高并发
    ctx.semaphore = asyncio.Semaphore(semaphore_limit)
    ctx.outline = Outline(goal=idea)
    
    patch_llm_aask(ctx)
    
    logger.info(f"上下文初始化完成。信号量限制: {semaphore_limit}")

    # --- 3. 团队组建 ---
    team = Team(context=ctx, use_mgx=False)
    team.hire([ChiefPM(), Scheduler(), Executor(), Archiver()])

    # --- 4. 运行 (使用自定义的 while 循环) ---
    team.env.publish_message(Message(role="user", content=idea))

    try:
        while ctx.kwargs.successful_llm_calls < max_llm_calls:
            if team.env.is_idle:
                logger.info("环境已空闲，所有任务完成，提前结束运行。")
                scheduler = team.env.get_role("Scheduler")
                if scheduler:
                    completion_msg = Message(content="ALL_DOCUMENT_TASKS_COMPLETED", role="Scheduler", send_to="Archiver")
                    team.env.publish_message(completion_msg)
                    await team.env.run(k=1)
                break
            
            await team.env.run(k=1)
        
        if ctx.kwargs.successful_llm_calls >= max_llm_calls:
            logger.warning(f"已达到最大LLM调用次数 ({max_llm_calls})，流程终止。")

    except Exception as e:
        logger.error(f"团队运行期间发生异常: {e}", exc_info=True)
    finally:
        # 强制归档
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
    user_idea = "人工智能在历史研究的应用"
    asyncio.run(main(idea=user_idea, max_llm_calls=59))