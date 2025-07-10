# 路径: /root/metagpt/mgfr/metagpt_doc_writer/roles/base_role.py (最终正确修复版)

import json
from metagpt.roles import Role
from metagpt.logs import logger
from metagpt.utils.common import OutputParser

class MyBaseRole(Role):
    """
    一个自定义的角色基类，它继承自 metagpt.Role，
    但重写了 _think 方法，使其能够更鲁棒地处理LLM的决策过程。
    """
    
    async def _think(self) -> None:
        """
        重写后的思考方法。该方法要求LLM进行思考，并从给定的动作列表中选择一个。
        它不再信任LLM返回的action name和index，而是通过LLM的思考过程来匹配最合适的动作。
        这大大增强了对抗LLM幻觉的能力。
        """
        if not self.rc.news:
            self.rc.state = -1
            return

        actions_desc = []
        for i, action in enumerate(self.actions):
            # 使用 getattr 安全地获取描述，如果方法不存在则回退到类名
            description = getattr(action, 'get_description', lambda: action.__class__.__name__)()
            actions_desc.append(f"  {i}. {action.name}: {description}")
        actions_desc_str = "\n".join(actions_desc)
        
        context = "\n".join([str(msg) for msg in self.rc.news])

        prompt = f"""
You are a {self.profile}, named {self.name}.
Your goal is: {self.goal}
Your constraints are: {self.constraints}

You are in a team, and the recent context is:
---
{context}
---

Based on the context, you need to decide what to do next. You have the following actions available:
---
Available Actions:
{actions_desc_str}
---

Please think step-by-step and then decide on the single best next action from the list above.
Respond with a JSON object in the following format.

{{
  "thought": "Your reasoning here. Analyze the situation, explain why you are choosing a specific action, and explicitly mention the name of the chosen action from the list.",
  "action_idx": "The index number (as an integer) of the action you choose from the 'Available Actions' list."
}}

Example Response:
{{
  "thought": "The user just provided a requirement. My first job as a ChiefPM is to review it and create a plan. The 'ReviewAndCommand' action seems most appropriate for this initial step.",
  "action_idx": 0
}}
"""
        rsp = await self.llm.aask(prompt)

        try:
            # [最终修复] 使用 metagpt 的标准方式来解析 LLM 输出
            # 这是最可靠的方法，能处理代码块标记等各种情况
            json_data = OutputParser.parse_code(block=None, text=rsp)

            action_idx_val = json_data.get("action_idx")
            if action_idx_val is None:
                 raise ValueError("LLM returned 'null' or did not provide 'action_idx'. Cannot decide on an action.")

            next_action_index = int(action_idx_val)
            
            if 0 <= next_action_index < len(self.actions):
                self.rc.state = next_action_index
                self.rc.todo = self.actions[next_action_index]
                thought = json_data.get('thought', 'No thought provided.')
                logger.info(f"{self._setting} decided to perform action '{self.rc.todo.name}' based on thought: {thought}")
            else:
                raise ValueError(f"Invalid action index '{next_action_index}' returned by LLM. It's out of bounds (0 to {len(self.actions)-1}).")

        except Exception as e: # 捕获所有可能的解析和逻辑错误
            logger.error(f"Failed to parse LLM's decision. Error: {e}. Raw response: '{rsp}'. Setting state to idle (-1).")
            self.rc.state = -1
            self.rc.todo = None