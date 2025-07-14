# /root/metagpt/mgfr/metagpt_doc_writer/actions/create_plan.py (最终版)

import json
from metagpt.actions import Action
from metagpt.utils.common import OutputParser
from metagpt_doc_writer.schemas.doc_structures import Plan
from metagpt.logs import logger

CREATE_PLAN_PROMPT = """
You are an expert project manager. Your task is to break down the user's high-level goal into a detailed, step-by-step plan.
The user wants: "{goal}"

Based on this goal, create a sequence of tasks. Each task must have:
- A unique `task_id`.
- A clear `instruction` describing what to do.
- An `action_type` chosen from the following list: ["RESEARCH", "WRITE", "REVIEW"].
- A `use_tools` list, containing any tools needed from this list: ["web_search"]. For most tasks, especially "RESEARCH", this is recommended. For other tasks, it's likely an empty list [].
- A list of `dependent_task_ids`. The first task has no dependencies.

Respond ONLY with a valid JSON object. Do not add any other text or comments.

Example:
{{
  "goal": "Write a tutorial about pytest",
  "tasks": [
    {{
      "task_id": "task_1",
      "instruction": "Research the key features and common use cases of pytest.",
      "action_type": "RESEARCH",
      "use_tools": ["web_search"],
      "dependent_task_ids": []
    }},
    {{
      "task_id": "task_2",
      "instruction": "Create a detailed outline for the pytest tutorial based on the research.",
      "action_type": "WRITE",
      "use_tools": [],
      "dependent_task_ids": ["task_1"]
    }}
  ]
}}
"""

class CreatePlan(Action):
    async def run(self, goal: str) -> Plan:
        prompt = CREATE_PLAN_PROMPT.format(goal=goal)
        plan_json_str = await self._aask(prompt)
        
        try:
            data_dict = OutputParser.parse_code(text=plan_json_str)
            if isinstance(data_dict, str):
                data_dict = json.loads(data_dict)
            
            plan = Plan(**data_dict)
            plan.task_map = {task.task_id: task for task in plan.tasks}
            
            logger.info("✅ LLM successfully generated a valid Plan object.")
            logger.info(plan.model_dump_json(indent=2))
            return plan
        
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.error(f"❌ LLM output failed validation. Error: {e}", exc_info=True)
            logger.error(f"Raw LLM output:\n---\n{plan_json_str}\n---")
            raise