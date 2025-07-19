# hierarchical/actions/write_section.py
import sys
from pathlib import Path

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# -----------------

from metagpt.actions import Action
from metagpt.logs import logger
from hierarchical.schemas import Section

PROMPT_TEMPLATE = """
You are an expert technical writer. Write the full content for the following section.
Be comprehensive, clear, and professional. The content should be in Markdown format.

Section Title: "{title}"
Section Should Cover: (This is a placeholder, in the future context will be richer)
---
{goal}
---

Now, write the full content for the section "{title}".
"""

class WriteSection(Action):
    name: str = "WriteSection"
    
    async def run(self, section: Section, goal: str) -> str:
        prompt = PROMPT_TEMPLATE.format(title=section.title, goal=goal)
        logger.info(f"Writing content for section '{section.title}' with LLM...")
        content = await self._aask(prompt)
        return content