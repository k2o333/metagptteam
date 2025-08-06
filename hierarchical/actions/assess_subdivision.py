import sys
import json
from pathlib import Path
from typing import Any, Dict
import re

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))

from metagpt.actions import Action
from metagpt.logs import logger


class AssessSubdivision(Action):
    def __init__(self, name: str = "assess_subdivision", context: Any = None, llm: Any = None):
        super().__init__(name=name, context=context, llm=llm)

    async def run(self, chapter_title: str, chapter_content: str, parent_context: str, research_summary: str, **kwargs) -> Dict[str, Any]:
        prompt = f"""
You are an intelligent document outline assessor. Your task is to determine if a given chapter should be further subdivided into sub-chapters.

Consider the following information:

Chapter Title: {chapter_title}

Chapter Content (summary/excerpt): {chapter_content}

Parent Context (from higher-level sections): {parent_context}

Research Summary (relevant findings for this topic): {research_summary}

Based on the existing information, is it meaningful and would it provide valuable new details to plan sub-chapters for this section? 

Respond with a JSON object in the format: {{"should_subdivide": true/false, "reason": "<your reasoning>"}}.
"""
        
        logger.info(f"Assessing subdivision for chapter: {chapter_title}")
        decision_str = await self._aask(prompt)
        
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', decision_str, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                decision = json.loads(json_str)
                if "should_subdivide" not in decision or "reason" not in decision:
                    raise ValueError("Invalid JSON response from LLM.")
                return decision
            else:
                raise ValueError("No JSON found in LLM response.")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}. Response: {decision_str}")
            return {"should_subdivide": False, "reason": f"LLM returned invalid JSON: {decision_str}"}
        except ValueError as e:
            logger.error(f"Invalid decision format from LLM: {e}. Response: {decision_str}")
            return {"should_subdivide": False, "reason": f"LLM returned invalid format: {decision_str}"}