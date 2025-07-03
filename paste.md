# Problematic Files Content

---

## File: mgfr/metagpt_doc_writer/prompts/self_reflection_prompt.py

```python
from string import Template

SELF_REFLECTION_PROMPT_TEMPLATE = Template("""
You are a meticulous Quality Critic. Your task is to review a piece of writing based on an original request.

**Original Request**:
"""
$request
"""

**Generated Output**:
"""
$output
"""

---
Please perform the following actions and respond in a single, valid JSON object:
1.  **Evaluate**: Score the output from 1 to 5 on three criteria:
    a) **Completeness**: Does it fully address all aspects of the original request?
    b) **Clarity**: Is the language clear, concise, and easy to understand?
    c) **Accuracy**: Is the information factually correct and logically sound?
2.  **Suggest**: Provide a brief, actionable suggestion for the single most important improvement. If no improvements are needed, state "None".
3.  **Revise**: If the total score is less than 13, provide a revised, improved version of the output. Otherwise, the value should be an empty string.

**Your JSON Response**:
"""
")
```

---

## File: mgfr/metagpt_doc_writer/actions/write_section.py

```python

from metagpt.actions import Action
from metagpt_doc_writer.schemas.doc_structures import ApprovedTask, DraftSection
from metagpt.schema import Message
from metagpt.utils.common import OutputParser
from metagpt_doc_writer.prompts.self_reflection_prompt import SELF_REFLECTION_PROMPT_TEMPLATE
import json

class WriteSection(Action):
    async def run(self, task: ApprovedTask) -> DraftSection:
        # Generate initial draft
        initial_prompt = f"""
        You are a technical writer. Write a draft section based on the following approved task:

        Title: {task.chapter_title}
        Context: {task.refined_task.context}
        Goals: {', '.join(task.refined_task.goals)}
        Acceptance Criteria: {', '.join(task.refined_task.acceptance_criteria)}

        Your draft should be comprehensive and directly address all goals and acceptance criteria.
        """
        initial_draft_rsp = await self._aask(initial_prompt)
        initial_draft_content = initial_draft_rsp.content

        # Self-reflection and refinement
        refined_draft_content = await self._reflect(initial_draft_content, task)

        return DraftSection(
            chapter_id=task.chapter_title, # Using title as ID for simplicity
            content=refined_draft_content
        )

    async def _reflect(self, draft_content: str, task: ApprovedTask) -> str:
        request_str = f"""
        Title: {task.chapter_title}
        Context: {task.refined_task.context}
        Goals: {', '.join(task.refined_task.goals)}
        Acceptance Criteria: {', '.join(task.refined_task.acceptance_criteria)}
        """
        reflection_prompt = SELF_REFLECTION_PROMPT_TEMPLATE.safe_substitute(request=request_str, output=draft_content)
        
        reflection_rsp = await self._aask(reflection_prompt)
        
        try:
            reflection_data = OutputParser.extract_struct(reflection_rsp.content, dict)
            # Calculate total score
            completeness = reflection_data.get('Evaluate', {}).get('Completeness', 0)
            clarity = reflection_data.get('Evaluate', {}).get('Clarity', 0)
            accuracy = reflection_data.get('Evaluate', {}).get('Accuracy', 0)
            total_score = completeness + clarity + accuracy

            if total_score < 13 and reflection_data.get('Revise'):
                return reflection_data['Revise']
            else:
                return draft_content
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing reflection JSON: {e}")
            return draft_content # Return original content if parsing fails

```

---

## File: mgfr/tests/actions/test_write_section.py

```python
import pytest
from metagpt_doc_writer.actions.write_section import WriteSection
from metagpt_doc_writer.schemas.doc_structures import ApprovedTask, RefinedTask
from metagpt.provider.base_llm import BaseLLM
from metagpt.schema import Message
import json

@pytest.mark.asyncio
async def test_write_section_with_reflection(mocker):
    # Mock the LLM for initial draft generation
    mock_initial_draft_content = "This is an initial draft with some flaws."
    mock_initial_draft_message = Message(content=mock_initial_draft_content)

    # Mock the LLM for self-reflection (first call - low score, needs revision)
    mock_reflection_response_low_score = {
        "Evaluate": {"Completeness": 2, "Clarity": 2, "Accuracy": 2}, # Total 6, < 13
        "Suggest": "Improve clarity and add more details.",
        "Revise": "This is the revised and improved draft."
    }
    mock_reflection_message_low_score = Message(content=json.dumps(mock_reflection_response_low_score))

    # Mock the LLM for self-reflection (second call - high score, no revision needed)
    mock_reflection_response_high_score = {
        "Evaluate": {"Completeness": 5, "Clarity": 5, "Accuracy": 5}, # Total 15, >= 13
        "Suggest": "None",
        "Revise": ""
    }
    mock_reflection_message_high_score = Message(content=json.dumps(mock_reflection_response_high_score))

    # Create a mock LLM instance
    mock_llm = mocker.Mock(spec=BaseLLM)
    mock_llm.aask.side_effect = [
        mock_initial_draft_message,  # First call for initial draft
        mock_reflection_message_low_score, # Second call for reflection (low score)
        mock_initial_draft_message,  # Third call for initial draft (for second test case)
        mock_reflection_message_high_score # Fourth call for reflection (high score)
    ]

    # Create an ApprovedTask instance
    approved_task = ApprovedTask(
        chapter_title="Test Chapter",
        refined_task=RefinedTask(
            chapter_title="Test Chapter",
            context="Context for testing",
            goals=["Goal 1", "Goal 2"],
            acceptance_criteria=["Criteria 1", "Criteria 2"]
        )
    )

    # Test case 1: Low score, should return revised draft
    action = WriteSection(llm=mock_llm)
    draft_section = await action.run(approved_task)

    assert draft_section.content == mock_reflection_response_low_score["Revise"]
    assert mock_llm.aask.call_count == 2 # Initial draft + reflection
    mock_llm.aask.reset_mock()

    # Test case 2: High score, should return original draft
    action = WriteSection(llm=mock_llm)
    draft_section = await action.run(approved_task)

    assert draft_section.content == mock_initial_draft_content
    assert mock_llm.aask.call_count == 2 # Initial draft + reflection
```

---

## File: mgfr/run.py

```python

import asyncio
from metagpt.team import Team
from metagpt.schema import Message
from metagpt_doc_writer.roles.chief_pm import ChiefPM
from metagpt_doc_writer.roles.task_dispatcher import TaskDispatcher
from metagpt_doc_writer.roles.task_refiner import TaskRefiner
from metagpt_doc_writer.roles.technical_writer import TechnicalWriter
from metagpt_doc_writer.roles.doc_assembler import DocAssembler
from metagpt_doc_writer.roles.changeset_generator import ChangeSetGenerator
from metagpt_doc_writer.roles.doc_modifier import DocModifier
from metagpt_doc_writer.schemas.doc_structures import ProjectPlan

async def main(idea: str):
    """
    This is a simplified orchestration. A real implementation would be more complex,
    with more sophisticated message passing and state management.
    """
    team = Team()
    team.hire([
        ChiefPM(),
        TaskDispatcher(),
        TaskRefiner(),
        TechnicalWriter(),
        DocAssembler(),
        ChangeSetGenerator(),
        DocModifier(),
    ])

    # For this simplified test, we'll manually pass messages
    # In a real scenario, the Team would manage the message flow based on role subscriptions
    team.run_project(idea)
    await team.run()

if __name__ == "__main__":
    asyncio.run(main("Write a simple tutorial about pytest."))
```

---

## File: mgfr/tests/test_full_pipeline_integration.py

```python

import pytest
from unittest.mock import patch
from metagpt.team import Team
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from run import main

@pytest.mark.asyncio
async def test_full_pipeline_integration(tmp_path):
    # Mock the OUTPUT_PATH in run.py to use a temporary directory
    with patch("run.OUTPUT_PATH", tmp_path):
        await main("Write a simple tutorial about pytest.")
        
        # Verify actual file output
        output_files = list(tmp_path.glob("*.md"))
        assert len(output_files) > 0 
        assert "pytest" in output_files[0].read_text()
```

---

## File: mgfr/metagpt_doc_writer/roles/technical_writer.py

```python

from metagpt.roles import Role
from metagpt.schema import Message
from metagpt_doc_writer.actions.write_section import WriteSection
from metagpt_doc_writer.schemas.doc_structures import ApprovedTask, DraftSection

class TechnicalWriter(Role):
    name: str = "TechnicalWriter"
    profile: str = "Technical Writer"
    goal: str = "Write high-quality technical documentation"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Pass the LLM instance to the WriteSection action
        self.set_actions([WriteSection(llm=self.llm)])
        self._watch({ApprovedTask}) # Watches for approved tasks

    async def _act(self) -> Message:
        # In a real scenario, this would be triggered by a message containing an ApprovedTask.
        # We would then run the WriteSection action.
        print("TechnicalWriter is acting...")
        # Placeholder for real implementation
        approved_task_msg = self.rc.memory.get_by_class(ApprovedTask)[-1]
        draft_section = await self.actions[0].run(approved_task_msg.instruct_content)
        return Message(content="Draft section written", instruct_content=draft_section)
```
