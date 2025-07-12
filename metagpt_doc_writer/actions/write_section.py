# /root/metagpt/mgfr/metagpt_doc_writer/actions/write_section.py (最终版)

import re
import asyncio
import json
from string import Template
from typing import Optional

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.utils.common import OutputParser
from metagpt_doc_writer.schemas.doc_structures import DraftSection, ApprovedTask
from metagpt_doc_writer.mcp.manager import MCPManager

# 将 self-reflection prompt 模板直接放在这里，减少文件依赖
SELF_REFLECTION_PROMPT_TEMPLATE = Template("""
You are a meticulous Quality Critic. Your task is to review a piece of writing based on an original request.
**Original Request**:
'''
$request
'''
**Generated Output**:
'''
$output
'''
---
Please perform the following actions and respond in a single, valid JSON object:
1.  **Evaluate**: Score the output from 1 to 5 on three criteria: Completeness, Clarity, Accuracy.
2.  **Suggest**: Provide a brief, actionable suggestion for the single most important improvement. If no improvements are needed, state "None".
3.  **Revise**: If the total score is less than 13, provide a revised, improved version of the output. Otherwise, the value should be an empty string.
**Your JSON Response**:
""")

class WriteSection(Action):
    name: str = "WriteSection"

    def __init__(self, **kwargs):
        # Action 初始化时保持简单，它将在运行时从其 owner(Role) 获取所需依赖
        super().__init__(**kwargs)

    async def run(self, approved_task: ApprovedTask) -> DraftSection:
        """
        Executes the full "research -> write -> reflect" process for a section.
        """
        # 从 owner Role 动态获取配置和依赖
        use_llm = getattr(self.owner, 'llm_activation', {}).get(self.name, False)
        mcp_manager: Optional[MCPManager] = getattr(self.owner, 'mcp_manager', None)
        can_use_mcp_tool = getattr(self.owner, 'can_use_mcp_tool', lambda x: False)

        logger.info(f"Executing WriteSection for: '{approved_task.chapter_title}'")

        if not use_llm:
            logger.warning(f"WriteSection is using MOCK data for '{approved_task.chapter_title}'.")
            mock_content = f"## {approved_task.chapter_title}\n\nThis is mocked content. To generate real content, set 'WriteSection: true' in config2.yaml."
            return DraftSection(chapter_id=approved_task.chapter_title, content=mock_content)

        # 1. 研究阶段 (Research Phase)
        research_context = ""
        if mcp_manager and can_use_mcp_tool("resolve-library-id") and can_use_mcp_tool("get-library-docs"):
            try:
                main_keyword = "autogen"
                logger.info(f"Attempting to use Context7 MCP tool for keyword: '{main_keyword}'")
                
                lib_id_result_str = await mcp_manager.call_tool(tool_name="resolve-library-id", args={"libraryName": main_keyword})
                
                match = re.search(r"(/[\w-]+/[\w-]+)", lib_id_result_str)
                lib_id = match.group(1) if match else None

                if lib_id:
                    logger.info(f"Resolved library ID for '{main_keyword}': {lib_id}")
                    docs_result_str = await mcp_manager.call_tool(tool_name="get-library-docs", args={"libraryId": lib_id})
                    research_context = f"\n\n### Sourced Documentation from Context7:\n\n{docs_result_str}\n\n"
                    logger.info(f"Successfully retrieved documentation for '{lib_id}' from Context7.")
                else:
                    logger.warning(f"Could not resolve library ID for '{main_keyword}'.")
            except Exception as e:
                logger.error(f"An error occurred during Context7 research phase: {e}", exc_info=True)
                research_context = "\n\n### Note: Research via Context7 failed.\n\n"
        else:
            logger.info("MCP Manager not available or tool permission denied for this role. Skipping research phase.")

        # 2. 写作阶段 (Writing Phase)
        task_details = (
            f"**Chapter Title**: {approved_task.chapter_title}\n"
            f"**Primary Goal**: {', '.join(approved_task.refined_task.goals)}\n"
            f"**Key Context**: {approved_task.refined_task.context}\n"
            f"**Acceptance Criteria**: {', '.join(approved_task.refined_task.acceptance_criteria)}\n"
        )
        
        writing_prompt = f"""You are an expert technical writer creating a guide. Based on the following task details and sourced documentation, write a comprehensive, clear, and accurate section.

**TASK DETAILS:**
---
{task_details}
---

{research_context}

Now, write the full, well-structured content for this section in Markdown.
"""

        logger.info("Calling LLM to generate initial draft...")
        initial_draft = await self._aask(writing_prompt)
        
        # 3. 自我反思阶段 (Reflection Phase)
        logger.info(f"Performing self-reflection on the draft...")
        final_content = await self._self_reflect_and_revise(approved_task.refined_task.goals, initial_draft)

        return DraftSection(chapter_id=approved_task.chapter_title, content=final_content)

    async def _self_reflect_and_revise(self, request_goals: list, initial_draft: str) -> str:
        prompt = SELF_REFLECTION_PROMPT_TEMPLATE.substitute(request=json.dumps(request_goals), output=initial_draft)
        reflection_str = await self._aask(prompt)
        try:
            reflection_obj = OutputParser.parse_code(text=reflection_str, lang="json")
            if isinstance(reflection_obj, str):
                reflection_obj = json.loads(reflection_obj)
            if isinstance(reflection_obj, dict) and reflection_obj.get("Revise") and reflection_obj.get("Revise").strip():
                logger.info("Self-reflection resulted in a revision.")
                return reflection_obj["Revise"]
        except Exception as e:
            logger.warning(f"Could not parse self-reflection response, using initial draft. Error: {e}")
        
        logger.info("Self-reflection concluded that the initial draft is sufficient.")
        return initial_draft