
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
import json

# Mock metagpt.config2.config to prevent ValidationError during import
# This needs to be done BEFORE any metagpt modules are imported that might trigger config loading
class MockLLMConfig:
    api_key = "sk-dummy-key"
    api_type = "openai"
    model = "gpt-4o-mini"
    base_url = "https://api.openai.com/v1"

class MockConfig:
    llm = MockLLMConfig()

# Directly patch the config object if it's already loaded or will be loaded
# This is a bit fragile and depends on metagpt's internal import order.
# A more robust solution would involve setting environment variables before the process starts.
try:
    import metagpt.config2
    metagpt.config2.config = MockConfig()
except ImportError:
    pass # metagpt.config2 might not be imported yet, or not found

# Set a dummy key to bypass the config check during initialization
os.environ["OPENAI_API_KEY"] = "sk-dummy"

from metagpt.schema import Message
from metagpt.utils.token_counter import TokenCost
from metagpt.team import Team # Needed for Archiver's serialize mock

from metagpt_doc_writer.actions.generate_changeset import GenerateChangeSet
from metagpt_doc_writer.roles.performance_monitor import PerformanceMonitor
from metagpt_doc_writer.roles.archiver import Archiver
from metagpt_doc_writer.schemas.doc_structures import ReviewNotes, FullDraft, FinalDelivery, ProjectArchived

async def run_generate_changeset_demo():
    print("--- Running GenerateChangeSet Demo ---")
    mock_llm = AsyncMock()
    # Simulate LLM returning a valid changeset
    mock_llm.aask.return_value = json.dumps({
        "changes": [
            {"operation": "REPLACE_BLOCK", "anchor_id": "anc123", "new_content": "Updated content.", "comment": "Demo change."}
        ]
    })

    action = GenerateChangeSet(llm=mock_llm)
    review_notes = ReviewNotes(feedback="Please update the first paragraph.")
    full_draft = FullDraft(content="[anchor-id::anc123]Original content.")

    try:
        changeset = await action.run(review_notes, full_draft)
        print(f"Generated ChangeSet: {changeset.json(indent=2)}")
        assert len(changeset.changes) > 0
    except Exception as e:
        print(f"GenerateChangeSet failed: {e}")
    print("--- GenerateChangeSet Demo Finished ---\n")

async def run_performance_monitor_demo():
    print("--- Running PerformanceMonitor Demo ---")
    monitor = PerformanceMonitor()

    # Simulate messages with token costs and execution times
    msg1 = Message(
        content="Task 1 completed",
        cause_by="metagpt_doc_writer.actions.WriteSection",
        token_cost=TokenCost(prompt_tokens=100, completion_tokens=50, total_cost=0.001)
    )
    setattr(msg1, 'execution_time', 0.5)

    msg2 = Message(
        content="Task 2 completed",
        cause_by="metagpt_doc_writer.actions.RefineTask",
        token_cost=TokenCost(prompt_tokens=200, completion_tokens=100, total_cost=0.002)
    )
    setattr(msg2, 'execution_time', 1.2)

    await monitor._observe(msg1)
    await monitor._observe(msg2)

    report = monitor.get_performance_report()
    print("Performance Report:\n" + json.dumps(report, indent=2))
    assert report['overall']['total_llm_tokens'] == 450
    assert report['overall']['total_llm_cost_usd'] == pytest.approx(0.003) # Using pytest.approx for float comparison
    print("--- PerformanceMonitor Demo Finished ---
")

async def run_archiver_demo():
    print("--- Running Archiver Demo ---")
    # Create a dummy FinalDelivery
    dummy_output_dir = Path("./temp_output_for_archive_demo")
    dummy_output_dir.mkdir(exist_ok=True)
    dummy_file1 = dummy_output_dir / "final_doc.md"
    dummy_file2 = dummy_output_dir / "report.json"
    dummy_file1.write_text("# Final Document")
    dummy_file2.write_text(json.dumps({"status": "ok"}))

    final_delivery = FinalDelivery(file_paths=[str(dummy_file1), str(dummy_file2)])

    # Mock the Archiver's rc.env.team for serialization
    mock_team = MagicMock(spec=Team)
    mock_team.serialize = AsyncMock() # Mock the async serialize method

    mock_env = MagicMock()
    mock_env.team = mock_team

    archiver = Archiver(archive_path="./temp_archive_demo")
    archiver.rc.memory.add(Message(content="Project Idea: Demo Project")) # Simulate project idea message
    archiver.rc.memory.add(Message(content="Final Delivery", instruct_content=final_delivery))
    archiver.rc.env = mock_env # Inject the mocked environment

    try:
        result_msg = await archiver._act()
        print(f"Archiver Result: {result_msg.content}")
        assert "Project archived to" in result_msg.content
        mock_team.serialize.assert_called_once()

        # Clean up dummy files and directories
        shutil.rmtree(dummy_output_dir)
        # The actual archive directory will be created by Archiver, check its existence
        # and then clean up. The name is dynamic, so we'll just check if it was created.
        # For a real test, you'd capture the exact path from result_msg.content
        print("Archiver demo cleanup complete.")
    except Exception as e:
        print(f"Archiver demo failed: {e}")
    print("--- Archiver Demo Finished ---
")

async def main():
    await run_generate_changeset_demo()
    await run_performance_monitor_demo()
    await run_archiver_demo()

if __name__ == "__main__":
    # Ensure pytest.approx is available for the PerformanceMonitor demo
    try:
        import pytest
    except ImportError:
        print("pytest is not installed. PerformanceMonitor demo might have issues with float comparison.")
        class PytestMock:
            def approx(self, value):
                return value
        pytest = PytestMock()

    asyncio.run(main())
