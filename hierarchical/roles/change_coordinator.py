import sys
import json
from pathlib import Path
from typing import Any, Dict

# --- Path Setup ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# ------------------

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.schema import Message
from hierarchical.roles.base_role import HierarchicalBaseRole
from hierarchical.actions.analyze_changes import AnalyzeChanges

class ChangeCoordinator(HierarchicalBaseRole):
    name: str = "ChangeCoordinator"
    profile: str = "Document Change Coordinator"
    goal: str = "Manage the document adaptation process by analyzing changes and dispatching rewrite tasks."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([AnalyzeChanges()])
        self._watch(["UserRequest"])
        self.document_content = None
        self.adaptation_instruction = None
        self.change_tasks = []
        self.current_task_index = 0

    async def _think(self) -> bool:
        self.rc.todo = None

        logger.debug(f"_think: document_content set: {bool(self.document_content)}")
        logger.debug(f"_think: adaptation_instruction set: {bool(self.adaptation_instruction)}")
        logger.debug(f"_think: change_tasks: {self.change_tasks}")
        logger.debug(f"_think: current_task_index: {self.current_task_index}")
        logger.debug(f"_think: len(change_tasks): {len(self.change_tasks) if self.change_tasks else 0}")

        # 1. Process initial UserRequest if present and document_content is not yet set
        if self.rc.news and not self.document_content:
            for msg in self.rc.news:
                if msg.cause_by == "UserRequest":
                    try:
                        content = json.loads(msg.content)
                        self.document_content = content.get("document_content")
                        self.adaptation_instruction = content.get("adaptation_instruction")
                        logger.info("Received new document adaptation request and stored content/instruction.")
                        self.rc.news.clear() # Clear news after processing
                        # After processing the initial request, re-evaluate the state to set the next todo
                        # This ensures that ANALYZE_CHANGES is set in the same _think call
                        return await self._think() 
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in UserRequest: {msg.content}")
                        continue
        
        # 2. Determine the next todo based on internal state
        if self.document_content and self.adaptation_instruction and not self.change_tasks:
            self.rc.todo = "ANALYZE_CHANGES"
            logger.debug(f"ChangeCoordinator thinking: Ready to ANALYZE_CHANGES. TODO set to: {self.rc.todo}")
            return True

        elif self.change_tasks and self.current_task_index < len(self.change_tasks):
            self.rc.todo = "DISPATCH_REWRITE_TASK"
            logger.debug(f"ChangeCoordinator thinking: Found pending rewrite tasks. TODO set to: {self.rc.todo}")
            return True

        elif self.change_tasks and self.current_task_index >= len(self.change_tasks):
            self.rc.todo = "SIGNAL_COMPLETION"
            logger.debug(f"ChangeCoordinator thinking: All tasks completed. TODO set to: {self.rc.todo}")
            return True

        logger.debug("ChangeCoordinator thinking: No new requests or pending tasks. Idling.")
        return False

    async def _act(self) -> Message:
        # Always call _think first to update self.rc.todo based on current state
        await self._think()
        logger.info(f"--- {self.name} is acting with todo: '{self.rc.todo}' ---")

        if self.rc.todo == "ANALYZE_CHANGES":
            analyze_action = self.actions[0] # Assuming AnalyzeChanges is the first action
            if not self.document_content or not self.adaptation_instruction:
                logger.error("Document content or adaptation instruction missing for analysis.")
                return Message(content="Error: Missing document content or instruction.")

            self.change_tasks = await self._execute_action(
                analyze_action,
                document_content=self.document_content,
                adaptation_instruction=self.adaptation_instruction
            )
            logger.info(f"Analyzed changes. Found {len(self.change_tasks)} tasks.")
            logger.debug(f"ChangeCoordinator: self.change_tasks after AnalyzeChanges: {self.change_tasks}")
            if not self.change_tasks:
                return Message(content="No changes needed or identified.", role=self.profile, send_to="User")
            
            # After analysis, re-trigger _think to dispatch tasks
            # The next call to _act will then pick up DISPATCH_REWRITE_TASK
            return Message(content="Changes analyzed. Ready to dispatch tasks.", role=self.profile, send_to="ChangeCoordinator")

        elif self.rc.todo == "DISPATCH_REWRITE_TASK":
            task = self.change_tasks[self.current_task_index]
            logger.info(f'Dispatching rewrite task: {task.get("rewrite_task")}')
            
            # Here, you would typically send this task to another role (e.g., a Writer or Editor role)
            # For now, we'll simulate completion and move to the next task.
            # In a real scenario, this would involve a message to another role and waiting for its response.
            
            # Simulate task completion
            self.current_task_index += 1
            logger.info(f"Simulated completion of task {self.current_task_index}/{len(self.change_tasks)}.")
            return Message(content=f"Task {self.current_task_index} dispatched and simulated complete.", role=self.profile, send_to="ChangeCoordinator")

        elif self.rc.todo == "SIGNAL_COMPLETION":
            logger.success("All document adaptation tasks completed.")
            return Message(content="Document adaptation process successfully completed.", role=self.profile, send_to="User")

        return Message(content="Unknown task, idling.")