import asyncio
import argparse
from pathlib import Path
import sys
import json
import yaml
import shutil

# Add the root of the MetaGPT project to the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # This should be /root/metagpt/mghier
sys.path.insert(0, str(PROJECT_ROOT))

from metagpt.context import Context
from metagpt.llm import LLM
from metagpt.config2 import Config
from hierarchical.roles.change_coordinator import ChangeCoordinator
from hierarchical.roles.section_applier import SectionApplier
from metagpt.schema import Message
from hierarchical.utils_pkg.version_control import VersionControl
from metagpt.team import Team


async def main(doc_path: str, prompt: str):
    print(f"Starting document adaptation for {doc_path} with prompt: {prompt}")
    
    # Validate that the document is a .md file
    doc_path_obj = Path(doc_path)
    if not doc_path_obj.exists():
        raise FileNotFoundError(f"Document file not found: {doc_path}")
        
    if doc_path_obj.suffix != '.md':
        raise ValueError(f"Document must be a .md file, got: {doc_path_obj.suffix}")
    
    # Create workspace directory if it doesn't exist
    workspace_dir = PROJECT_ROOT / "workspace"
    workspace_dir.mkdir(exist_ok=True)
    
    # Copy the original document to workspace
    workspace_doc_path = workspace_dir / doc_path_obj.name
    shutil.copy2(doc_path_obj, workspace_doc_path)
    
    # Create a versioned copy of the document in workspace
    versioned_doc_path = VersionControl.create_versioned_copy(workspace_doc_path)
    print(f"Created versioned copy: {versioned_doc_path}")

    # 1. Initialize LLM and Context
    llm = LLM()
    ctx = Context(llm=llm)

    # 2. Load configuration from YAML files
    global_config_path = Path("/root/.metagpt/config2.yaml")
    local_config_path = PROJECT_ROOT / "configs" / "local_config.yaml"
    
    # Load and merge configurations
    global_config = Config.from_yaml_file(global_config_path)
    raw_global_config_data = yaml.safe_load(global_config_path.read_text()) or {}
    local_config_data = yaml.safe_load(local_config_path.read_text()) or {}
    merged_config_data = {**raw_global_config_data, **local_config_data}
    
    # Set custom configuration in context
    ctx.kwargs.custom_config = merged_config_data
    ctx.kwargs.strategy_config = local_config_data

    # 3. Initialize McpManager from configuration if available
    mcp_manager = None
    try:
        from mcp.manager import MCPManager
        mcp_servers_config = merged_config_data.get("mcp_servers", {})
        role_mcp_bindings = merged_config_data.get("role_mcp_bindings", {})
        
        if mcp_servers_config:
            mcp_manager = MCPManager(server_configs=mcp_servers_config)
            await mcp_manager.start_servers()
            ctx.mcp_manager = mcp_manager
            print("MCP Manager initialized successfully")
        else:
            print("No MCP servers configured, continuing without MCP")
    except ImportError:
        print("MCP module not available, continuing without MCP")
    except Exception as e:
        print(f"Failed to initialize MCP Manager: {e}")
        mcp_manager = None

    # 4. Create team with ChangeCoordinator and SectionApplier roles
    team = Team(context=ctx, use_mgx=False)  # Disable mgx to avoid the AttributeError
    coordinator = ChangeCoordinator(context=ctx)
    applier = SectionApplier(context=ctx)
    
    if mcp_manager:
        coordinator.context.mcp_manager = mcp_manager
        applier.context.mcp_manager = mcp_manager
        
    team.hire([coordinator, applier])

    # 5. Simulate user input to the coordinator
    # In a real scenario, this would be a message from a user or another role
    document_content = Path(versioned_doc_path).read_text()
    initial_message = Message(
        content=json.dumps({
            "document_content": document_content, 
            "adaptation_instruction": prompt,
            "document_path": str(versioned_doc_path)
        }),
        role="User",
        cause_by="UserRequest"
    )
    team.env.publish_message(initial_message)

    # 6. Run the team's act method repeatedly
    max_iterations = 20 # Safety break to prevent infinite loops
    current_iteration = 0
    final_response = None

    while current_iteration < max_iterations:
        current_iteration += 1
        print(f"Team acting (Iteration {current_iteration})...")
        await team.run(1)  # Fixed: use positional argument instead of k=1
        
        # Check for completion messages
        try:
            # Access messages properly from the Memory object
            messages = list(team.env.history)  # This should convert Memory to a list of messages
            if messages:
                latest_msg = messages[-1]
                # Check if latest_msg is a Message object or tuple
                if hasattr(latest_msg, 'content'):
                    content = latest_msg.content
                elif isinstance(latest_msg, tuple) and len(latest_msg) > 0:
                    # If it's a tuple, the content might be in the first element
                    content = latest_msg[0] if hasattr(latest_msg[0], 'content') else str(latest_msg[0])
                else:
                    content = str(latest_msg)
                    
                # Check for more comprehensive completion indicators
                completion_indicators = [
                    "successfully completed",
                    "Unknown task, idling",
                    "Successfully applied section change",
                    "Document adaptation process finished"
                ]
                
                if any(indicator in content for indicator in completion_indicators):
                    final_response = latest_msg
                    print(f"Process completed at iteration {current_iteration}")
                    break
        except Exception as e:
            print(f"Error accessing messages: {e}")
            # Continue with the loop even if we can't access messages properly
                
        await asyncio.sleep(0.1) # Small delay to prevent busy-waiting

    if final_response:
        print(f"Document adaptation process finished. Final response: {final_response.content}")
    else:
        print("Document adaptation process finished without a final response.")
        # Even if we don't have a final response, let's check the output file
        print("Checking the output file for content changes...")
        if versioned_doc_path.exists():
            output_content = versioned_doc_path.read_text()
            print(f"Output file content:\n{output_content}")
        else:
            print("Output file was not created.")

    # 7. Clean up
    if mcp_manager:
        await mcp_manager.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Adapt a document based on a prompt.")
    parser.add_argument("--doc_path", type=str, required=True, help="Path to the document to adapt.")
    parser.add_argument("--prompt", type=str, required=True, help="Prompt describing the adaptation to perform.")
    args = parser.parse_args()

    asyncio.run(main(args.doc_path, args.prompt))