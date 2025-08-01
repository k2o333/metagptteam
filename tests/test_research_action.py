import asyncio
import pytest
import sys
from pathlib import Path

# Add the project root to the path to allow imports from mghier and metagpt
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from mghier.hierarchical.actions.research import Research
from metagpt.context import Context
from metagpt.llm import LLM
from mghier.mcp.manager import MCPManager
from mghier.hierarchical.roles.chief_pm import ChiefPM
from metagpt.schema import Message

@pytest.mark.asyncio
async def test_research_action_e2e():
    """
    An end-to-end test for the Research action, now run via ChiefPM.
    """
    # 1. Initialize the LLM 
    llm = LLM()

    # 2. Initialize the McpManager with server configs from the project
    server_configs = {
        "context7": {
            "command": "npx",
            "args": ["-y", "@upstash/context7-mcp@latest", "--transport", "stdio"],
            "timeout": 40
        }
    }
    mcp_manager = MCPManager(server_configs=server_configs)
    await mcp_manager.start_servers() # Start the servers

    # 3. Create an instance of the ChiefPM role with the context and mcp_manager
    ctx = Context(llm=llm, mcp_manager=mcp_manager)
    chief_pm = ChiefPM(context=ctx)
    user_query = "what is metagpt framework?"
    research_action_instance = Research(context=ctx)
    research_results_by_query = await chief_pm._execute_action(
        research_action_instance, 
        queries=[user_query]
    )

    # 5. Assert the results
    assert user_query in research_results_by_query
    result = research_results_by_query[user_query]
    assert result["status"] == "success"
    assert "metagpt" in result["final_answer"].lower()

    # 6. Clean up
    await mcp_manager.close()