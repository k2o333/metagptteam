#!/bin/bash
export METAGPT_LLM_API_TYPE=openai
export METAGPT_LLM_API_KEY=mock-key-for-testing

/root/metagpt/mgenv/bin/python scripts/test_doc_assembler.py
