import asyncio
import os
import sys
from pathlib import Path

# Add project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Add the path to the metagpt library
sys.path.append('/root/metagpt')

from mghier.hierarchical.actions.research import Research
from hierarchical.context import HierarchicalContext
from metagpt.llm import LLM
from mghier.mcp.manager import MCPManager

async def main():
    # 1. Initialize the LLM and Context
    llm = LLM()
    ctx = HierarchicalContext(llm=llm)

    # 2. Initialize the McpManager with the context
    mcp_manager = MCPManager(server_configs={})
    ctx.mcp_manager = mcp_manager

    # 3. Create an instance of the Research action with the context
    research_action = Research(context=ctx)

    # You might need to set up a dummy DocRAGEngine if your action requires it.
    # For now, let's assume it can handle not having one for some queries.
    # If not, you'll need to initialize and set it.
    # research_action.set_docrag_engine(...) 

    # 4. Define the queries and tool descriptions
    queries = ["What is the capital of France?"]
    tool_descriptions = await mcp_manager.get_tools_description()

    # 5. Run the action
    results = await research_action.run(queries=queries, tool_descriptions=tool_descriptions)

    # 6. Print the results
    print("Research Results:")
    for query, result in results.items():
        print(f"Query: {query}")
        print(f"  Status: {result.get('status')}")
        print(f"  Source: {result.get('source')}")
        print(f"  Final Answer: {result.get('final_answer')}")
        print("-" * 20)

if __name__ == "__main__":
    # Since run is an async function, we use asyncio to run it
    asyncio.run(main())
