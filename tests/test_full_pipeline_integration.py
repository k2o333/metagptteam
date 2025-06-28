
import pytest
from unittest.mock import patch
from metagpt.team import Team
from metagpt_doc_writer.run import main

@pytest.mark.asyncio
async def test_full_pipeline_integration():
    # This is a placeholder for a more comprehensive integration test.
    # A real test would involve mocking the LLM and asserting the final output.
    with patch('asyncio.run') as mock_run:
        await main("Write a simple tutorial about pytest.")
        # In a real test, you would assert that the team runs and produces the expected output.
        # For now, we just assert that the main function is called.
        mock_run.assert_called_once()
