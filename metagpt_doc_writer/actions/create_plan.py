# /root/metagpt/mgfr/metagpt_doc_writer/actions/create_plan.py

import json
from metagpt.actions import Action
from metagpt.utils.common import OutputParser
from metagpt_doc_writer.schemas.doc_structures import Plan
from metagpt.logs import logger
from typing import ClassVar

# 【核心修正】: 将 "ReflectAndOptimize" 彻底替换为 "Revise"
CREATE_PLAN_PROMPT: ClassVar[str] = """
You are a master strategist and project manager. Your task is to create a sophisticated, step-by-step execution plan based on a user's high-level goal.

**The user wants: "{goal}"**

Create the plan as a valid JSON object. For each task, you MUST define the following fields:
- `task_id`: A unique identifier, e.g., "task_1".
- `instruction`: A clear, actionable instruction for an AI agent.
- `action_type`: **This is CRITICAL. You MUST use the exact ClassName-style strings from this list**: ["Research", "Write", "Review", "Revise"].
- `target_snippet_id`: For a new `Write` task, create a unique ID (e.g., "installation_guide"). For `Review` or `Revise` tasks, you MUST use the `target_snippet_id` of the content they are targeting. For `Research` tasks, this should be `null`.
- `use_tools`: A list of tools required, e.g., ["web_search"].
- `dependent_task_ids`: A list of `task_id`s that must be completed before this task can start.

**Example of a good plan:**
{{
  "goal": "Write a tutorial about pytest",
  "tasks": [
    {{
      "task_id": "task_1",
      "instruction": "Research the core features of pytest.",
      "action_type": "Research",
      "target_snippet_id": null,
      "use_tools": ["web_search"],
      "dependent_task_ids": []
    }},
    {{
      "task_id": "task_2",
      "instruction": "Write the introduction section for the pytest tutorial.",
      "action_type": "Write",
      "target_snippet_id": "pytest_intro",
      "use_tools": [],
      "dependent_task_ids": ["task_1"]
    }},
    {{
      "task_id": "task_3",
      "instruction": "Review the introduction for clarity.",
      "action_type": "Review",
      "target_snippet_id": "pytest_intro",
      "use_tools": [],
      "dependent_task_ids": ["task_2"]
    }},
    {{
      "task_id": "task_4",
      "instruction": "Based on the review, revise the introduction.",
      "action_type": "Revise",
      "target_snippet_id": "pytest_intro",
      "dependent_task_ids": ["task_3"]
    }}
  ]
}}

Now, generate the JSON plan for the user's goal. Respond with ONLY the valid JSON object.
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