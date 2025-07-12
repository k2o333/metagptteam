# /root/metagpt/mgfr/scripts/run.py (最终完整版)

import sys
import asyncio
import json
from pathlib import Path
import yaml
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from metagpt.logs import logger
from metagpt.team import Team
from metagpt.schema import Message
from metagpt.actions.add_requirement import UserRequirement

from metagpt_doc_writer.mcp.manager import MCPManager
from metagpt_doc_writer.roles import (
    Archiver,
    ChangeSetGenerator,
    ChiefPM,
    DocAssembler,
    DocModifier,
    GroupPM,
    PerformanceMonitor,
    QAAgent,
    TaskDispatcher,
    TaskRefiner,
    TechnicalWriter,
)
from metagpt_doc_writer.schemas.doc_structures import (
    FinalDelivery,
    UserRequirement as CustomUserRequirement,
)

LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
logger.add(LOGS_DIR / "run.log", rotation="10 MB", retention="1 week", level="INFO")

OUTPUT_PATH = PROJECT_ROOT / "outputs"
OUTPUT_PATH.mkdir(exist_ok=True)

ARCHIVE_PATH = PROJECT_ROOT / "archive"
ARCHIVE_PATH.mkdir(exist_ok=True)


def find_config_path() -> Path:
    """Helper to find the configuration file."""
    if "METAGPT_CONFIG_PATH" in os.environ:
        return Path(os.environ["METAGPT_CONFIG_PATH"])
    home_config = Path.home() / ".metagpt/config2.yaml"
    if home_config.exists():
        return home_config
    project_config = PROJECT_ROOT / "configs" / "config2.yaml"
    if project_config.exists():
        return project_config
    return None


async def main(idea: str):
    logger.info(f"Starting document generation process for: '{idea}'")

    config_yaml_path = find_config_path()
    if not config_yaml_path or not config_yaml_path.exists():
        logger.error("MetaGPT configuration file (config2.yaml) not found.")
        sys.exit(1)

    full_config = {}
    try:
        with open(config_yaml_path, "r", encoding="utf-8") as f:
            full_config = yaml.safe_load(f)
        logger.info(f"Full configuration loaded successfully from '{config_yaml_path}'")
    except Exception as e:
        logger.error(f"Failed to load or parse YAML configuration: {e}")
        sys.exit(1)

    # Let MetaGPT load its standard configs
    os.environ["METAGPT_CONFIG_PATH"] = str(config_yaml_path)
    from metagpt.config2 import Config
    main_config = Config.default()

    # Load our custom configurations from the full dictionary
    team_settings = full_config.get("team_settings", {})
    llm_activation = full_config.get("llm_activation", {})
    mcp_server_configs = full_config.get("mcp_servers", {})
    mcp_bindings = full_config.get("role_mcp_bindings", {})

    # Override investment to "disable" billing-based termination
    investment = 10000.0
    n_round = team_settings.get("n_round", 200)

    logger.info(f"Billing effectively disabled (investment set to ${investment}).")
    logger.info(f"Team run settings: n_round={n_round}.")
    logger.info(f"LLM Activation: {llm_activation}")
    logger.info(f"MCP Bindings: {mcp_bindings}")
    logger.info(f"MCP Servers to start: {list(mcp_server_configs.keys())}")


    manager = MCPManager(server_configs=mcp_server_configs)
    await manager.start_servers()

    team = Team(investment=investment, n_round=n_round)

    # Pass all necessary configurations to the roles that need them.
    # Roles will then pass these down to their actions.
    shared_configs = {
        "llm_activation": llm_activation,
        "mcp_manager": manager,
        "mcp_bindings": mcp_bindings,
    }

    team.hire([
        ChiefPM(**shared_configs),
        GroupPM(**shared_configs),
        TaskDispatcher(),
        TaskRefiner(**shared_configs),
        TechnicalWriter(**shared_configs),
        DocAssembler(),
        DocModifier(),
        QAAgent(**shared_configs),
        ChangeSetGenerator(**shared_configs),
        PerformanceMonitor(),
        Archiver(archive_path=str(ARCHIVE_PATH)),
    ])
    logger.info("Team hired successfully.")

    logger.info(f"Publishing initial user requirement: '{idea}'")

    cause_by_str = f"{UserRequirement.__module__}.{UserRequirement.__name__}"
    initial_message = Message(
        content=idea,
        instruct_content=CustomUserRequirement(content=idea),
        role="Human",
        cause_by=cause_by_str,
        send_to="ChiefPM",
    )

    team.env.publish_message(initial_message)

    logger.info(f"Starting multi-agent run...")
    await team.run()

    logger.info(f"Document generation process for '{idea}' finished.")

    # ... (Reporting and archiving logic remains the same)
    monitor = next((role for role in team.env.roles.values() if isinstance(role, PerformanceMonitor)), None)
    if monitor:
        report = monitor.get_performance_report()
        report_path = OUTPUT_PATH / "performance_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Performance report saved to {report_path}")

    archiver = next((role for role in team.env.roles.values() if isinstance(role, Archiver)), None)
    if archiver and archiver.rc.memory.get():
        logger.info("Triggering Archiver...")
        final_doc_placeholder = OUTPUT_PATH / "final_document.md"
        if not final_doc_placeholder.exists():
            final_doc_placeholder.touch()
        
        final_delivery_msg = Message(
            content="Document is finalized.",
            instruct_content=FinalDelivery(document_path=str(final_doc_placeholder))
        )
        await archiver.run(final_delivery_msg)
        
    await manager.close()


if __name__ == "__main__":
    idea_from_args = " ".join(sys.argv[1:])
    if not idea_from_args:
        idea_from_args = "Write a detailed technical guide on how to install autogen and implement a concurrent multi-expert discussion using its GroupChat feature."

    try:
        asyncio.run(main(idea=idea_from_args))
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)