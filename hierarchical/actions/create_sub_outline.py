# hierarchical/actions/create_sub_outline.py
import sys
from pathlib import Path
from typing import List, Optional

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
# --- 【核心修正】修正这里的拼写错误 ---
sys.path.insert(0, str(METAGPT_ROOT)) 
# -----------------

from metagpt.actions import Action
from metagpt.logs import logger
from hierarchical.schemas import Section

class CreateSubOutline(Action):
    """
    Action to create a detailed outline for a given parent section.
    In this phase, it returns mocked data.
    """
    name: str = "CreateSubOutline"

    async def run(self, parent_section: Optional[Section] = None) -> List[Section]:
        """
        :param parent_section: The section to create a sub-outline for. If None, creates a top-level outline.
        :return: A list of new sub-sections.
        """
        is_top_level = parent_section is None
        parent_display_id = f"{parent_section.display_id}." if parent_section else ""
        parent_id = parent_section.section_id if parent_section else None
        new_level = parent_section.level + 1 if parent_section else 1
        
        if is_top_level:
            logger.info("MOCK: Generating top-level outline...")
            mock_titles = ["1. Introduction", "2. Core Concepts", "3. Conclusion"]
        else:
            logger.info(f"MOCK: Generating sub-outline for '{parent_section.title}'...")
            mock_titles = [f"Sub-section A for {parent_section.title}", f"Sub-section B for {parent_section.title}"]

        new_sections = []
        for i, title in enumerate(mock_titles):
            display_id = f"{parent_display_id}{i + 1}" if not is_top_level else str(i + 1)
            sec = Section(
                display_id=display_id,
                title=title,
                level=new_level,
                parent_id=parent_id,
                status="PENDING_WRITE" # New sections are ready to be written
            )
            new_sections.append(sec)
        
        logger.info(f"Generated {len(new_sections)} new sections.")
        return new_sections