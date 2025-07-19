# hierarchical/actions/create_sub_outline.py
import sys
from pathlib import Path
from typing import List, Optional
import json

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# -----------------

from metagpt.actions import Action
from metagpt.logs import logger
# --- 【核心修正】导入 CodeParser 而不是 OutputParser ---
from metagpt.utils.common import CodeParser
from hierarchical.schemas import Section

PROMPT_TEMPLATE = """
You are an expert technical writer. Based on the document goal and the parent section, create a sub-outline.
The document's main goal is: "{goal}"

You are creating a sub-outline for the parent section:
Title: "{parent_title}"
Level: {parent_level}
Content (if any):
---
{parent_content}
---

Please generate a list of 2-4 concise, logical sub-section titles for this parent section.
Respond ONLY with a valid JSON list of strings wrapped in a ```json code block. Example:
```json
[
    "Sub-section 1 Title",
    "Sub-section 2 Title"
]
```
"""
# ... (imports and class definition) ...

class CreateSubOutline(Action):
    name: str = "CreateSubOutline"

    async def run(self, parent_section: Optional[Section] = None, goal: str = "") -> List[Section]:
        # --- 【核心修正】所有后续代码都应在此方法内部，并保持正确的缩进 ---
        is_top_level = parent_section is None
        
        if is_top_level:
            prompt = f'You are an expert project manager. Create a top-level outline for a document about "{goal}". Generate 3-5 main chapter titles. Respond ONLY with a valid JSON list of strings wrapped in a ```json code block.'
            logger.info("Generating top-level outline with LLM...")
        else:
            prompt = PROMPT_TEMPLATE.format(
                goal=goal,
                parent_title=parent_section.title,
                parent_level=parent_section.level,
                parent_content=parent_section.content or "N.A"
            )
            logger.info(f"Generating sub-outline for '{parent_section.title}' with LLM...")

        response_str = await self._aask(prompt)
        
        try:
            parsed_json_str = CodeParser.parse_code(text=response_str, lang="json")
            titles = json.loads(parsed_json_str)
        except Exception as e:
            logger.error(f"Failed to parse outline titles from LLM response: {e}. Raw response: '{response_str}'. Using fallback.")
            titles = ["Default Section 1 (Parsing Error)", "Default Section 2"]

        parent_display_id = f"{parent_section.display_id}." if parent_section else ""
        parent_id = parent_section.section_id if parent_section else None
        new_level = parent_section.level + 1 if parent_section else 1
        
        new_sections = []
        for i, title in enumerate(titles):
            clean_title = title.split('. ', 1)[-1]
            display_id = f"{parent_display_id}{i + 1}" if not is_top_level else str(i + 1)
            sec = Section(display_id=display_id, title=clean_title, level=new_level, parent_id=parent_id, status="PENDING_WRITE")
            new_sections.append(sec)
        
        logger.info(f"LLM generated {len(new_sections)} new sections.")
        
        return new_sections