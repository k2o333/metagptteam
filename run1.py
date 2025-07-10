# /root/metagpt/mgfr/run.py (最终强制加载版)

"""
Main entry point for the Multi-Agent Document Writing System.
This script orchestrates the entire team of agents to generate a document based on a user's idea.
"""
# =======================================================================================
#  CRITICAL: CONFIGURATION SETUP
#  This block MUST be at the very top of the file, before any metagpt imports.
# =======================================================================================
import sys
import os
from pathlib import Path
import yaml  # 确保导入 yaml

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

CONFIG_PATH = PROJECT_ROOT / "configs" / "config2.yaml"
if not CONFIG_PATH.exists():
    raise FileNotFoundError(f"Configuration file not found at: {CONFIG_PATH}")

# 不再需要设置环境变量，因为我们将手动加载
# os.environ['METAGPT_CONFIG_PATH'] = str(CONFIG_PATH)

# =======================================================================================
#  REGULAR IMPORTS
# =======================================================================================
import asyncio
import json

from metagpt.config2 import Config
from metagpt.logs import logger
from metagpt.team import Team
from metagpt.provider.openai_api import OpenAILLM
from metagpt.schema import Message

from metagpt_doc_writer.roles import (
    ChiefPM, GroupPM, TaskDispatcher, TaskRefiner, TechnicalWriter,
    QAAgent, ChangeSetGenerator, DocAssembler, DocModifier,
    PerformanceMonitor, Archiver
)
from metagpt_doc_writer.tools import WebSearch, DiagramGenerator
from metagpt_doc_writer.utils.tool_registry import ToolRegistry

# --- Configuration Section ---
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
logger.add(LOGS_DIR / "log.txt", rotation="10 MB", retention="1 week")

OUTPUT_PATH = PROJECT_ROOT / "outputs"
OUTPUT_PATH.mkdir(exist_ok=True)

ARCHIVE_PATH = PROJECT_ROOT / "archive"
ARCHIVE_PATH.mkdir(exist_ok=True)

# =======================================================================================
#  MANUAL CONFIGURATION LOADING (绕过 Config.default())
# =======================================================================================
try:
    logger.info(f"Manually loading configuration from: {CONFIG_PATH}")
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    if not config_data or 'llm' not in config_data:
        raise ValueError("YAML file is empty or missing the 'llm' block.")

    # 使用加载的数据直接实例化 Config 对象
    main_config = Config(**config_data)
    
    # 将加载的配置设置为 metagpt 的全局配置，以防有其他模块依赖它
    Config.set_default_config(main_config)

    logger.info("Configuration manually loaded and set as default successfully.")
    logger.info(f"Effective LLM model from manual load: '{main_config.llm.model}'")
    logger.info(f"Effective Search type from manual load: '{main_config.search.api_type if main_config.search else 'N/A'}'")

except Exception as e:
    logger.error(f"FATAL: Failed to manually load or validate configuration from {CONFIG_PATH}. Error: {e}", exc_info=True)
    sys.exit(1)

# --- LLM INSTANTIATION ---
try:
    # 强制使用 'open_llm' 类型以支持自定义模型
    main_config.llm.api_type = "open_llm"
    
    llm_instance = OpenAILLM(config=main_config.llm)
    llm_strategy = llm_instance
    llm_execution = llm_instance
    llm_fast = llm_instance

    logger.info(f"LLM instance created. Model: '{llm_instance.model}', API Type: '{llm_instance.llm_config.api_type}'")
except Exception as e:
    logger.error(f"Failed to initialize LLM. Please check your 'llm' config block. Error: {e}", exc_info=True)
    sys.exit(1)


# --- Main Orchestration (保持不变) ---
async def main(idea: str, investment: float = 20.0, n_round: int = 15):
    logger.info(f"Starting document generation process for: '{idea}'")
    
    logger.info("Initializing tools...")
    try:
        web_search_tool = WebSearch(search_config=main_config.search)
        diagram_generator_tool = DiagramGenerator()
        tool_registry = ToolRegistry(tools=[web_search_tool, diagram_generator_tool])
        logger.info(f"Tool registry initialized with: {[t.schema.name for t in tool_registry._tools.values()]}")
    except Exception as e:
        logger.error(f"Failed to initialize tools. Please check 'search' config. Error: {e}", exc_info=True)
        tool_registry = ToolRegistry(tools=[]) 
        logger.warning("Continuing without web search tools.")

    logger.info("Hiring the agent team...")
    team = Team()
    team.hire([
        ChiefPM(llm=llm_strategy),
        GroupPM(llm=llm_strategy),
        TaskRefiner(llm=llm_strategy),
        TaskDispatcher(llm=llm_fast),
        TechnicalWriter(llm=llm_execution, tool_registry=tool_registry),
        QAAgent(llm=llm_strategy),
        ChangeSetGenerator(llm=llm_strategy),
        DocAssembler(output_path=str(OUTPUT_PATH)),
        DocModifier(),
        PerformanceMonitor(),
        Archiver(archive_path=str(ARCHIVE_PATH))
    ])
    logger.info("Team hired successfully.")

    team.invest(investment)
    team.run_project(idea)
    logger.info(f"Project '{idea}' is set up. Starting the run...")
    
    await team.run(n_round=n_round)
    logger.info(f"Document generation process for '{idea}' finished.")
    
    logger.info("Finalizing project: Generating performance report and archiving...")
    performance_monitor = team.get_role(role_id="PerformanceMonitor")
    if performance_monitor:
        report = performance_monitor.get_performance_report()
        report_path = OUTPUT_PATH / "performance_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Performance report saved to {report_path}")
        
    archiver = team.get_role(role_id="Archiver")
    if archiver:
        logger.info("Triggering Archiver...")
        await archiver.run()


# --- Script Entry Point (保持不变) ---
if __name__ == "__main__":
    user_idea = " ".join(sys.argv[1:])
    if not user_idea:
        user_idea = "Write a comprehensive tutorial about using pytest fixtures for testing Python applications."
        logger.info(f"No user idea provided. Using default: '{user_idea}'")

    try:
        asyncio.run(main(idea=user_idea))
    except Exception:
        logger.exception("An unexpected error occurred and terminated the main run:")