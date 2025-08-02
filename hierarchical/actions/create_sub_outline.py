# mghier/hierarchical/actions/create_sub_outline.py (真正完整的最终修复版)

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
from metagpt.utils.common import CodeParser
from hierarchical.schemas import Section

# 【修改】为PROMPT_TEMPLATE添加研究上下文的位置
PROMPT_TEMPLATE = """
You are an expert technical writer. Based on the document goal, research context, and the parent section, create a sub-outline.
The document's main goal is: "{goal}"

**Research Context (if any):**
---
{research_context}
---

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
    "Sub-section 1 Title based on Research",
    "Sub-section 2 Title"
]
```
"""

# 【新增】顶层大纲的Prompt模板
TOP_LEVEL_PROMPT_TEMPLATE = """
You are an expert project manager. Your task is to create a top-level outline for a document.

**Main Goal:**
"{goal}"

**Initial Research Context:**
---
{research_context}
---

Based on the goal and the provided research context, generate 3-5 main chapter titles for the document.
Respond ONLY with a valid JSON list of strings wrapped in a ```json code block.
"""

class CreateSubOutline(Action):
    # 【核心修复】移除 name 字段的直接赋值。
    # 基类 Action 的 @model_validator 会自动用类名 "CreateSubOutline" 来填充它。

    async def run(self, parent_section: Optional[Section] = None, goal: str = "", research_context: str = "N/A", **kwargs) -> List[Section]:
        is_top_level = parent_section is None
        
        if is_top_level:
            prompt = TOP_LEVEL_PROMPT_TEMPLATE.format(
                goal=goal,
                research_context=research_context
            )
            logger.info("Generating top-level outline with LLM, using research context...")
        else:
            prompt = PROMPT_TEMPLATE.format(
                goal=goal,
                research_context=research_context,
                parent_title=parent_section.title,
                parent_level=parent_section.level,
                parent_content=parent_section.content or "N.A"
            )
            logger.info(f"Generating sub-outline for '{parent_section.title}' with LLM, using research context...")

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
