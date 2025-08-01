import asyncio
import argparse
from pathlib import Path
import sys
import json

# Add the root of the MetaGPT project to the Python path
# This assumes the script is run from within the metagpt/mghier directory or its subdirectories
# or that /root/metagpt is already in PYTHONPATH.
# We explicitly add /root/metagpt to ensure mghier is importable as a package.
METAGPT_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent # This should be /root/metagpt
sys.path.insert(0, str(METAGPT_PROJECT_ROOT))

from metagpt.context import Context
from metagpt.llm import LLM
from mghier.mcp.manager import MCPManager
from mghier.hierarchical.roles.change_coordinator import ChangeCoordinator
from metagpt.schema import Message

async def main(doc_path: str, prompt: str):
    print(f"Starting document adaptation for {doc_path} with prompt: {prompt}")

    # 1. Initialize LLM and Context
    llm = LLM()
    ctx = Context(llm=llm)

    # 2. Initialize McpManager
    server_configs = {
        "context7": {
            "command": "npx",
            "args": ["-y", "@upstash/context7-mcp@latest", "--transport", "stdio"],
            "timeout": 40
        }
    }
    mcp_manager = MCPManager(server_configs=server_configs)
    await mcp_manager.start_servers()

    # 3. Create ChangeCoordinator role
    coordinator = ChangeCoordinator(context=ctx, mcp_manager=mcp_manager)

    # 4. Simulate user input to the coordinator
    # In a real scenario, this would be a message from a user or another role
    document_content = Path(doc_path).read_text()
    initial_message = Message(
        content=json.dumps({"document_content": document_content, "adaptation_instruction": prompt}),
        role="User",
        cause_by="UserRequest"
    )
    coordinator.rc.memory.add(initial_message)

    # 5. Run the coordinator's act method repeatedly
    max_iterations = 10 # Safety break to prevent infinite loops
    current_iteration = 0
    final_response = None

    while current_iteration < max_iterations:
        current_iteration += 1
        print(f"Coordinator acting (Iteration {current_iteration})...")
        response = await coordinator._act()
        
        if response:
            final_response = response
            print(f"Coordinator response: {response.content}")
            if "successfully completed" in response.content or "Unknown task, idling" in response.content:
                break
        else:
            print("Coordinator returned no response. Idling.")
            break
        await asyncio.sleep(0.1) # Small delay to prevent busy-waiting

    if final_response:
        print(f"Document adaptation process finished. Final response: {final_response.content}")
    else:
        print("Document adaptation process finished without a final response.")

    # 6. Clean up
    await mcp_manager.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Adapt a document based on a prompt.")
    parser.add_argument("--doc_path", type=str, required=True, help="Path to the document to adapt.")
    parser.add_argument("--prompt", type=str, required=True, help="Prompt describing the adaptation to perform.")
    args = parser.parse_args()

    asyncio.run(main(args.doc_path, args.prompt))