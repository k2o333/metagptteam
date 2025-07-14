# /root/metagpt/mgfr/metagpt_doc_writer/actions/create_plan.py (新增文件)

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
      "dependent_task_ids": []
    }},
    {{
      "task_id": "task_2",
      "instruction": "Create a detailed outline for the pytest tutorial based on the research.",
      "action_type": "WRITE",
      "dependent_task_ids": ["task_1"]
    }},
    {{
      "task_id": "task_3",
      "instruction": "Review the outline for clarity and completeness.",
      "action_type": "REVIEW",
      "dependent_task_ids": ["task_2"]
    }}
  ]
}}
"""

class CreatePlan(Action):
    async def run(self, goal: str) -> Plan:
        prompt = CREATE_PLAN_PROMPT.format(goal=goal)
        plan_json_str = await self._aask(prompt)
        
        try:
            # 简化解析，因为Prompt要求纯JSON
            data_dict = json.loads(OutputParser.parse_code(plan_json_str))
            plan = Plan(**data_dict)
            plan.task_map = {task.task_id: task for task in plan.tasks}
            return plan
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"LLM output failed validation for Plan: {e}", exc_info=True)
            raise