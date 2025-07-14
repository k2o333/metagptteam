# /root/metagpt/mgfr/metagpt_doc_writer/actions/create_module_outline.py (新增或更新)

import json
from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.utils.common import OutputParser
from mgfr.metagpt_doc_writer.schemas.doc_structures import ModuleOutline
from typing import ClassVar, Dict, Any, List

class CreateModuleOutline(Action):
    """
    Action to create a detailed outline for a given module title, potentially enhanced by RAG.
    """
    name: str = "CreateModuleOutline"
    
    # 定义一个 Prompt 模板
    PROMPT_TEMPLATE: ClassVar[str] = """
    You are an expert outline creator. Given a module title and optional research context,
    create a detailed, hierarchical outline for a technical documentation module.
    
    Module Title: "{module_title}"
    
    {research_context_placeholder}
    
    Provide the outline as a JSON object, with the module_title and a list of chapter titles.
    
    Example:
    {{
      "module_title": "Introduction to MetaGPT",
      "chapters": [
        "1.1 What is MetaGPT?",
        "1.2 Core Concepts",
        "1.3 Why Use MetaGPT?"
      ]
    }}
    """

    async def run(self, module_title: str, topic: str = "", research_context: str = "") -> ModuleOutline:
        logger.info(f"Action: Creating module outline for '{module_title}'...")

        research_context_str = ""
        if research_context:
            research_context_str = f"Here is some relevant research context:\n---\n{research_context}\n---\n"
        
        prompt = self.PROMPT_TEMPLATE.format(
            module_title=module_title,
            research_context_placeholder=research_context_str
        )
        
        response_str = await self._aask(prompt, system_msgs=["You are a helpful assistant that creates structured outlines."])
        
        try:
            data_dict = OutputParser.parse_code(text=response_str)
            if isinstance(data_dict, str): # In case OutputParser returns a string representation of JSON
                data_dict = json.loads(data_dict)
            
            outline = ModuleOutline(**data_dict)
            logger.info(f"Successfully created outline for module '{module_title}'. Chapters: {outline.chapters}")
            return outline
        except Exception as e:
            logger.error(f"Failed to parse LLM output into ModuleOutline for '{module_title}'. Error: {e}. Raw output: {response_str}", exc_info=True)
            # Fallback: return a basic outline to prevent pipeline breakage
            return ModuleOutline(module_title=module_title, chapters=[f"{module_title} - Section 1", f"{module_title} - Section 2"])