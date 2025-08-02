import sys
import json
from pathlib import Path
from typing import Any, Dict, List

# --- Path Setup ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# ------------------

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.utils.common import CodeParser

ANALYZE_CHANGES_PROMPT = """
You are an expert document analysis AI. Your task is to analyze a given document and a user's adaptation instruction, then identify specific sections that need to be modified. For each identified section, you must provide its exact location (start and end line/character) and a precise task description for rewriting or adapting that section.

**Document Content:**
---
{document_content}
---

**Adaptation Instruction:**
"{adaptation_instruction}"

**Instructions:**
1.  Carefully read the document content and the adaptation instruction.
2.  Identify all distinct parts of the document that need to be changed to fulfill the instruction.
3.  For each part, determine the exact `start_line`, `start_char`, `end_line`, and `end_char` (0-indexed) within the provided `document_content`.
4.  Provide a clear and concise `rewrite_task` for each identified part, describing exactly how that part should be modified.
5.  If no changes are needed, return an empty list.

Respond ONLY with a valid JSON list of objects, where each object represents a change. The format should be:
```json
[
  {
    "start_line": <int>,
    "start_char": <int>,
    "end_line": <int>,
    "end_char": <int>,
    "rewrite_task": "<string describing the rewrite task>"
  },
  // ... more change objects
]
```
Example:
```json
[
  {
    "start_line": 0,
    "start_char": 0,
    "end_line": 0,
    "end_char": 11,
    "rewrite_task": "Change 'Hello World' to 'Greetings Earth'"
  }
]
```
"""

class AnalyzeChanges(Action):
    def __init__(self, name: str = "Analyze Document Changes", context: Any = None, llm: Any = None):
        super().__init__(name=name, context=context, llm=llm)

    async def run(self, document_content: str, adaptation_instruction: str) -> List[Dict[str, Any]]:
        logger.info("Analyzing document for changes...")

        prompt = ANALYZE_CHANGES_PROMPT.format(
            document_content=document_content,
            adaptation_instruction=adaptation_instruction
        )

        response_str = await self._aask(prompt)
        
        try:
            parsed_json_str = CodeParser.parse_code(text=response_str, lang="json")
            changes = json.loads(parsed_json_str)
            logger.debug(f"AnalyzeChanges LLM decision: {changes}")
            return changes
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM decision for AnalyzeChanges. Error: {e}. Raw response: \n{response_str}")
            return [] # Return empty list on parsing error
