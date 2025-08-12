# /root/metagpt/mghier/hierarchical/actions/assess_research_necessity.py

import sys
import json
from pathlib import Path
from typing import Dict, Any

# --- Path Setup ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
# ------------------

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.utils.common import CodeParser

ASSESS_RESEARCH_PROMPT = """
You are a senior technical writer and research strategist. Your task is to analyze a rewrite instruction within the context of a larger document and determine if external research is necessary.

**Global Document Topic:**
"{global_topic}"

**Analyze the following specific task:**

1.  **Original Section Content (excerpt):**
    ---
    {section_content}
    ---

2.  **Rewrite Instruction:**
    "{rewrite_instruction}"

**Your Decision-Making Process:**
1.  Considering the global topic is '{global_topic}', does the instruction require new factual information, technical details (e.g., specific parameters, class names, function behaviors), or examples that are not present in the original local content?
2.  If research is needed, what is the most precise and effective search query (the "research topic")? This query MUST combine the global topic with specific terms from the instruction.
    -   *Good research topic:* "AutoGen MessageContext class"
    -   *Bad research topic:* "MessageContext" (too generic)

**Output Format:**
Respond ONLY with a valid JSON object in the following format:
```json
{{
  "should_research": <true_or_false>,
  "research_topic": "<The precise, context-aware topic to research, or an empty string>",
  "reason": "<A brief justification for your decision>"
}}
```
"""

class AssessResearchNecessity(Action):
    """An Action to decide if research is needed for a rewrite task, using global context."""
    
    async def run(self, global_topic: str, section_content: str, rewrite_instruction: str, **kwargs) -> Dict[str, Any]:
        """
        Analyzes the task and determines if research is required.

        Returns:
            A dictionary with 'should_research', 'research_topic', and 'reason'.
        """
        prompt = ASSESS_RESEARCH_PROMPT.format(
            global_topic=global_topic,
            section_content=section_content[:1000],  # Truncate for efficiency
            rewrite_instruction=rewrite_instruction
        )
        
        response_str = await self._aask(prompt)
        
        try:
            parsed_json_str = CodeParser.parse_code(text=response_str, lang="json")
            decision = json.loads(parsed_json_str)
            logger.info(f"Research assessment decision: {decision}")
            return decision
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse research assessment decision: {e}. Defaulting to no research.")
            return {"should_research": False, "research_topic": "", "reason": "Failed to parse LLM decision."}