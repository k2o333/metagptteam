# mghier/hierarchical/actions/rewrite_section.py

import sys
import json
from pathlib import Path
from typing import Dict, Any

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# -----------------

from metagpt.actions import Action
from metagpt.logs import logger

REWRITE_PROMPT_TEMPLATE = """
You are an expert editor and technical writer. Your task is to rewrite a specific section of a document according to a given instruction.

**ORIGINAL DOCUMENT SECTION:**
---
{original_text}
---

**REWRITE INSTRUCTION:**
"{rewrite_instruction}"

**FULL DOCUMENT CONTEXT:**
---
{full_document}
---

**INSTRUCTIONS:**
1. Carefully read the original text section and the rewrite instruction.
2. Rewrite the section according to the instruction, maintaining the overall document's tone and style.
3. Make sure your rewrite fits seamlessly with the surrounding content.
4. Respond ONLY with the rewritten text. Do not include any explanations, markdown, or additional text.
5. Preserve any existing formatting unless the instruction specifically asks to change it.
"""

class RewriteSection(Action):
    name: str = "RewriteSection"
    
    async def run(self, original_text: str, rewrite_instruction: str, full_document: str = "", **kwargs) -> str:
        """
        Rewrites a section of text based on a specific instruction.
        
        Args:
            original_text: The original text to rewrite
            rewrite_instruction: The instruction for how to rewrite the text
            full_document: The full document context (optional)
            **kwargs: Additional parameters (ignored)
            
        Returns:
            The rewritten text
        """
        prompt = REWRITE_PROMPT_TEMPLATE.format(
            original_text=original_text,
            rewrite_instruction=rewrite_instruction,
            full_document=full_document
        )
        logger.info(f"Rewriting section with instruction: {rewrite_instruction[:100]}...")
        content = await self._aask(prompt)
        return content.strip()