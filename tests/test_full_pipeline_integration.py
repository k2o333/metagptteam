# /root/metagpt/mgfr/tests/test_full_pipeline_integration.py

import pytest
from unittest.mock import patch
from metagpt.team import Team
import sys
import os

# 确保能从上级目录导入 run 模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from run import main

@pytest.mark.asyncio
async def test_full_pipeline_integration(mocker):
    # Mock DocAssembler's file writing to prevent actual file creation during tests
    # FIX: Corrected a typo from "metagagpt" to "metagpt"
    mocker.patch("metagpt_doc_writer.roles.doc_assembler.DocAssembler._finalize_document", return_value="Final document content.")
    mocker.patch("metagpt_doc_writer.roles.archiver.Archiver._act", return_value=None)
    
    # Mock the LLM to return predictable content.
    # 修改为 mock 更具体的 OpenAILLM.aask 方法，这更稳妥
    mocker.patch("metagpt.provider.openai_api.OpenAILLM.aask", return_value="Mocked LLM Response")

    # FIX: Mock the SearchEngine class to prevent validation error during WebSearch init.
    # The validation fails because the default config requires an API key, which isn't available in tests.
    # This patch prevents the real SearchEngine.__init__ from running.
    mocker.patch("metagpt_doc_writer.tools.web_search.SearchEngine")

    # Mock the search tool's run method to avoid actual web searches during tests
    mocker.patch("metagpt_doc_writer.tools.web_search.WebSearch.run", return_value="Mocked search results.")

    # Run the main function
    await main("Write a simple tutorial about pytest.")

    # The main purpose of this test is to ensure the pipeline runs without errors.
    # A simple assertion to confirm the test ran to completion.
    assert True