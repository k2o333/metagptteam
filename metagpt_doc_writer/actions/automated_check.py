# 文件路径: /root/metagpt/mgfr/metagpt_doc_writer/actions/automated_check.py (已修正)

import json
from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.utils.common import OutputParser
from metagpt_doc_writer.schemas.doc_structures import FullDraft, QAReport
from typing import ClassVar # <-- 【关键】导入ClassVar

# 【关键修正】: 使用 ClassVar 注解
QA_PROMPT: ClassVar[str] = """
You are an expert Quality Assurance Agent. Your task is to review the following document draft based on a predefined checklist and provide a structured QA report in JSON format.

**Checklist:**
1.  **Terminology Consistency**: Are key terms used consistently throughout the document?
2.  **Clarity and Conciseness**: Is the language clear, simple, and free of jargon?
3.  **Formatting**: Does the document follow standard Markdown formatting rules (e.g., proper headings, lists)?
4.  **Completeness**: Does the document appear complete, without obvious placeholder text like "[TBD]"?

**Document Draft to Review:**
---
{draft_content}
---

**Instructions:**
- For each issue you find, create a feedback item with a `feedback_type`, a `description` of the issue, and a `suggestion` for fixing it.
- If no issues are found, return an empty list for "feedbacks".
- Respond ONLY with a valid JSON object matching the QAReport schema.

**JSON Output Format:**
{{
  "feedbacks": [
    {{
      "feedback_type": "Clarity",
      "description": "The sentence '...' in the second paragraph is ambiguous.",
      "suggestion": "Rewrite the sentence to be more specific, for example: '...'"
    }}
  ]
}}
"""

class AutomatedCheck(Action):
    """
    An action to perform automated quality assurance checks on a document draft.
    """
    async def run(self, full_draft: FullDraft) -> QAReport:
        logger.info(f"Performing automated QA check on draft version {full_draft.version}...")

        prompt = QA_PROMPT.format(draft_content=full_draft.content)
        
        response_str = await self._aask(prompt)
        
        try:
            data_dict = OutputParser.parse_code(text=response_str)
            if isinstance(data_dict, str):
                data_dict = json.loads(data_dict)
            qa_report = QAReport(**data_dict)
            logger.info(f"QA check completed, found {len(qa_report.feedbacks)} issues.")
            return qa_report
        except Exception as e:
            logger.error(f"Failed to validate parsed dictionary into QAReport. Error: {e}. Parsed dict: {response_str}")
            return QAReport(feedbacks=[])