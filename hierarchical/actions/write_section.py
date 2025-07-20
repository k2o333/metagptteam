# hierarchical/actions/write_section.py
import sys
from pathlib import Path
from typing import Dict, Any # <-- 引入 Dict, Any

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# -----------------

from metagpt.actions import Action
from metagpt.logs import logger
from hierarchical.schemas import Section # Section is used in context construction, not directly in run signature

# --- 【核心修正】升级 Prompt 模板 ---
PROMPT_TEMPLATE = """
You are an expert technical writer. Your task is to write the body content for a specific section of a document.

**DOCUMENT'S MAIN GOAL:**
{goal}

**DOCUMENT STRUCTURE (BREADCRUMBS):**
{breadcrumbs}

**PARENT SECTION'S CONTENT:**
---
{parent_content}
---

**PRECEDING SIBLING SECTIONS (TITLES ONLY):**
---
{sibling_titles}
---

**INSTRUCTIONS:**
- Write the full body content for the section: **"{target_section_title}"**.
- Your content must be coherent with the parent section and avoid repeating topics from sibling sections.
- **DO NOT** include any section titles or headings (e.g., `#`, `##`, `###`) in your response.
- Start directly with the first sentence of the section's body.
"""

class WriteSection(Action):
    name: str = "WriteSection"
    
    # --- 【核心修正】run 方法现在接收一个 context 字典 ---
    async def run(self, context: Dict[str, Any]) -> str:
        prompt = PROMPT_TEMPLATE.format(
            goal=context.get("goal", "N/A"),
            breadcrumbs=context.get("breadcrumbs", "N/A"),
            parent_content=context.get("parent_content", "N/A (This is a top-level section)"),
            sibling_titles=context.get("sibling_titles", "None"),
            target_section_title=context.get("target_section_title", "N/A")
        )
        logger.info(f"Writing content for section '{context.get('target_section_title')}' with rich context...")
        content = await self._aask(prompt)
        return content.strip()