import sys
import json
import re
from pathlib import Path
from typing import Any, Dict, List
from typing_extensions import Annotated

# --- Path Setup ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# ------------------

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.utils.common import CodeParser


class AnalyzeHeaderChanges(Action):
    def __init__(self, name: str = "Analyze Document Header Changes", context: Any = None, llm: Any = None):
        super().__init__(name=name, context=context, llm=llm)
        
    async def run(self, document_content: str, adaptation_instruction: str, **kwargs) -> List[Dict[str, str]]:
        logger.info("Analyzing document headers for changes...")
        
        # Build the prompt with XML format instructions
        prompt = f"""
You are an expert document analysis AI. Your task is to analyze a given Markdown document and a user's adaptation instruction, then identify specific sections (based on their exact header strings) that need to be modified.

**Document Content:**
---
{document_content}
---

**Adaptation Instruction:**
"{adaptation_instruction}"

**Instructions:**
1. Carefully read the document content and the adaptation instruction.
2. Identify all distinct sections of the document that need to be changed to fulfill the instruction.
3. For each section, identify its EXACT full markdown heading string (including all # symbols and formatting).
4. Provide a clear and concise `rewrite_task` for each identified section, describing exactly how that section should be modified.
5. If no changes are needed, return an empty list.

You must provide your answer in the following XML format. Do not include any other text outside the XML tags.

<AnalysisResult>
    <HeaderBasedChange>
        <full_heading_string>THE_EXACT_MARKDOWN_HEADING_1</full_heading_string>
        <rewrite_task>YOUR_REWRITE_TASK_FOR_HEADING_1</rewrite_task>
    </HeaderBasedChange>
    <HeaderBasedChange>
        <full_heading_string>THE_EXACT_MARKDOWN_HEADING_2</full_heading_string>
        <rewrite_task>YOUR_REWRITE_TASK_FOR_HEADING_2</rewrite_task>
    </HeaderBasedChange>
    ...
</AnalysisResult>

Example:
<AnalysisResult>
    <HeaderBasedChange>
        <full_heading_string>### **1. 核心目标**</full_heading_string>
        <rewrite_task>将核心目标从"初步探索"修改为"实现生产级可用性"，并补充两个关键的性能指标。</rewrite_task>
    </HeaderBasedChange>
    <HeaderBasedChange>
        <full_heading_string>#### 1.2 相关技术</full_heading_string>
        <rewrite_task>在相关技术中增加对"向量数据库"的介绍。</rewrite_task>
    </HeaderBasedChange>
</AnalysisResult>
"""
        
        # Call the LLM
        response_str = await self._aask(prompt)
        
        # Parse the XML response
        try:
            result_list = self._parse_xml_response(response_str)
            logger.debug(f"AnalyzeHeaderChanges LLM decision: {result_list}")
            return result_list
        except Exception as e:
            logger.error(f"Failed to parse LLM decision for AnalyzeHeaderChanges. Error: {e}")
            return []
            
    def _parse_xml_response(self, response: str) -> List[Dict[str, str]]:
        """Parse the XML response from the LLM."""
        # Extract content between <AnalysisResult> tags
        analysis_result_match = re.search(r'<AnalysisResult>(.*?)</AnalysisResult>', response, re.DOTALL)
        if not analysis_result_match:
            return []
            
        analysis_content = analysis_result_match.group(1)
        
        # Find all HeaderBasedChange entries
        result_list = []
        header_changes = re.findall(r'<HeaderBasedChange>(.*?)</HeaderBasedChange>', analysis_content, re.DOTALL)
        
        for change in header_changes:
            # Extract full_heading_string
            heading_match = re.search(r'<full_heading_string>(.*?)</full_heading_string>', change, re.DOTALL)
            # Extract rewrite_task
            task_match = re.search(r'<rewrite_task>(.*?)</rewrite_task>', change, re.DOTALL)
            
            if heading_match and task_match:
                heading = heading_match.group(1).strip()
                task = task_match.group(1).strip()
                result_list.append({
                    "full_heading_string": heading,
                    "rewrite_task": task
                })
        
        return result_list