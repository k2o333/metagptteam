import sys
import json
import os
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

# --- Path Setup ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
# ------------------

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.schema import Message
from hierarchical.roles.base_role import HierarchicalBaseRole
from hierarchical.actions.analyze_header_changes import AnalyzeHeaderChanges
from hierarchical.actions.assess_subdivision import AssessSubdivision
from hierarchical.utils_pkg.version_control import VersionControl


class ChangeCoordinator(HierarchicalBaseRole):
    name: str = "ChangeCoordinator"
    profile: str = "Document Change Coordinator"
    goal: str = "Manage the document adaptation process by analyzing changes and dispatching rewrite tasks."
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([AnalyzeHeaderChanges(), AssessSubdivision()])
        self._watch(["UserRequest"])
        self.document_content = None
        self.document_path = None
        self.adaptation_instruction = None
        self.change_tasks = []
        self.current_task_index = 0
        self.outline = None
        self.task_queue = []
        self.status_file_path = None
        self.phase = "INIT"  # INIT, ANALYZE, REWRITE, APPLY, COMPLETE
        
    async def _think(self) -> bool:
        self.rc.todo = None
        
        logger.debug(f"_think: phase: {self.phase}")
        logger.debug(f"_think: document_content set: {bool(self.document_content)}")
        logger.debug(f"_think: adaptation_instruction set: {bool(self.adaptation_instruction)}")
        logger.debug(f"_think: task_queue: {self.task_queue}")
        logger.debug(f"_think: current_task_index: {self.current_task_index}")
        logger.debug(f"_think: rc.news: {self.rc.news}")
        
        # 1. Process initial UserRequest if present and document_content is not yet set
        if self.rc.news and not self.document_content:
            for msg in self.rc.news:
                if msg.cause_by == "UserRequest":
                    try:
                        content = json.loads(msg.content)
                        self.document_content = content.get("document_content")
                        self.document_path = content.get("document_path")
                        self.adaptation_instruction = content.get("adaptation_instruction")
                        logger.info("Received new document adaptation request and stored content/instruction.")
                        self.rc.news.clear() # Clear news after processing
                        self.phase = "ANALYZE"  # Directly move to ANALYZE phase
                        self.rc.todo = "ANALYZE_CHANGES"
                        logger.debug(f"ChangeCoordinator thinking: Ready to ANALYZE_CHANGES. TODO set to: {self.rc.todo}")
                        return True
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in UserRequest: {msg.content}")
                        continue
        
        # Determine next phase based on current state
        if self.phase == "INIT":
            self.rc.todo = "INITIALIZE"
            return True
            
        elif self.phase == "ANALYZE" and self.document_content and self.adaptation_instruction:
            self.rc.todo = "ANALYZE_CHANGES"
            logger.debug(f"ChangeCoordinator thinking: Ready to ANALYZE_CHANGES. TODO set to: {self.rc.todo}")
            return True
            
        elif self.phase == "REWRITE":
            # Check if there are pending rewrite tasks
            pending_rewrite_tasks = [task for task in self.task_queue if task.get("status") == "pending_rewrite"]
            if pending_rewrite_tasks:
                self.rc.todo = "DISPATCH_REWRITE_BATCH"
                return True
            else:
                # No more tasks to rewrite, move to apply phase
                self.phase = "APPLY"
                return await self._think()  # Recursively call to determine next todo
                
        elif self.phase == "APPLY":
            # Check if there are tasks ready to apply
            applying_tasks = [task for task in self.task_queue if task.get("status") == "rewriting" and "new_content" in task]
            if applying_tasks:
                self.rc.todo = "APPLY_CHANGES"
                return True
            else:
                # Check if all tasks are completed or if we're done
                completed_tasks = [task for task in self.task_queue if task.get("status") == "completed"]
                if len(self.task_queue) > 0 and len(completed_tasks) == len(self.task_queue):
                    self.phase = "COMPLETE"
                    return await self._think()  # Recursively call to determine next todo
                
        elif self.phase == "COMPLETE":
            self.rc.todo = "SIGNAL_COMPLETION"
            return True
            
        logger.debug("ChangeCoordinator thinking: No new requests or pending tasks. Idling.")
        return False
        
    async def _act(self) -> Message:
        # Always call _think first to update self.rc.todo based on current state
        await self._think()
        logger.info(f"--- {self.name} is acting with todo: '{self.rc.todo}' ---")
        
        if self.rc.todo == "INITIALIZE":
            # Check for existing status file to resume
            if self.document_path:
                doc_name = Path(self.document_path).stem
                self.status_file_path = Path(self.document_path).parent / f".{doc_name}.adapt_status.json"
                
                if self.status_file_path.exists():
                    # Load existing state
                    with open(self.status_file_path, 'r') as f:
                        state = json.load(f)
                    self.task_queue = state.get("task_queue", [])
                    self.phase = "APPLY"  # Continue from application phase
                    logger.info("Resumed from existing status file")
                else:
                    # Start fresh analysis
                    self.phase = "ANALYZE"
                    
            return Message(content="Initialized adaptation process.", role=self.profile, send_to="ChangeCoordinator")
            
        elif self.rc.todo == "ANALYZE_CHANGES":
            analyze_action = self.actions[0]  # AnalyzeHeaderChanges
            if not self.document_content or not self.adaptation_instruction:
                logger.error("Document content or adaptation instruction missing for analysis.")
                return Message(content="Error: Missing document content or instruction.")
                
            # Analyze changes using header-based approach
            self.change_tasks = await self._execute_action(
                analyze_action,
                document_content=self.document_content,
                adaptation_instruction=self.adaptation_instruction
            )
            
            logger.info(f"Analyzed changes. Found {len(self.change_tasks)} tasks.")
            
            # Validate all headings are unique
            heading_strings = [task["full_heading_string"] for task in self.change_tasks]
            if len(heading_strings) != len(set(heading_strings)):
                logger.error("Duplicate headings found in change tasks.")
                return Message(content="Error: Duplicate headings found in analysis.", role=self.profile, send_to="User")
                
            # Initialize task queue with statuses
            self.task_queue = []
            for task in self.change_tasks:
                task_with_status = task.copy()
                task_with_status["status"] = "pending_rewrite"
                self.task_queue.append(task_with_status)
                
            # Save state
            self._save_state()
            
            self.phase = "REWRITE"
            return Message(content="Changes analyzed and task queue initialized.", role=self.profile, send_to="ChangeCoordinator")
            
        elif self.rc.todo == "DISPATCH_REWRITE_BATCH":
            # Get all pending rewrite tasks
            pending_tasks = [task for task in self.task_queue if task.get("status") == "pending_rewrite"]
            
            if not pending_tasks:
                # No more tasks to rewrite, move to apply phase
                self.phase = "APPLY"
                return Message(content="All rewrite tasks dispatched.", role=self.profile, send_to="ChangeCoordinator")
                
            # In a real implementation, we would send these to an Executor role
            # For now, we'll simulate the rewriting
            logger.info(f"Dispatching {len(pending_tasks)} rewrite tasks.")
            
            # Update status of dispatched tasks
            for task in self.task_queue:
                if task.get("status") == "pending_rewrite":
                    task["status"] = "rewriting"
                    
            # Simulate rewriting by just marking as complete
            for task in self.task_queue:
                if task.get("status") == "rewriting":
                    task["new_content"] = f"<!-- Rewritten content for {task['full_heading_string']} based on task: {task['rewrite_task']} -->\nThis is simulated rewritten content."
                    
            # Save state
            self._save_state()
            
            # Move to APPLY phase since we've simulated the rewriting
            self.phase = "APPLY"
            
            return Message(content=f"Dispatched {len(pending_tasks)} rewrite tasks.", role=self.profile, send_to="ChangeCoordinator")
            
        elif self.rc.todo == "APPLY_CHANGES":
            # Find next task to apply
            for task in self.task_queue:
                if task.get("status") == "rewriting" and "new_content" in task:
                    # Create a message to send to SectionApplier
                    application_request = {
                        "target_heading_string": task['full_heading_string'],
                        "new_heading_and_content": task['new_content'],
                        "file_path": self.document_path
                    }
                    
                    # Send message to SectionApplier
                    application_message = Message(
                        content=json.dumps(application_request),
                        role=self.profile,
                        send_to="SectionApplier",
                        cause_by="SectionApplicationRequest"
                    )
                    self.rc.env.publish_message(application_message)
                    
                    logger.info(f"Sent section application request for heading: {task['full_heading_string']}")
                    
                    # Update task status to indicate it's being applied
                    task["status"] = "applying"
                    
                    # Save state
                    self._save_state()
                    
                    return Message(content=f"Sent application request for {task['full_heading_string']}", role=self.profile, send_to="ChangeCoordinator")
                    
            # If no more tasks to apply, move to complete phase
            self.phase = "COMPLETE"
            return Message(content="All changes applied.", role=self.profile, send_to="ChangeCoordinator")
            
        elif self.rc.todo == "SIGNAL_COMPLETION":
            # Check if all tasks are completed
            all_completed = all(task.get("status") == "completed" for task in self.task_queue)
            if all_completed:
                # Clean up status file
                if self.status_file_path and self.status_file_path.exists():
                    os.remove(self.status_file_path)
                    
                logger.success("All document adaptation tasks completed.")
                return Message(content="Document adaptation process successfully completed.", role=self.profile, send_to="User")
            else:
                logger.warning("Not all tasks completed, but signaling completion.")
                return Message(content="Document adaptation process completed with some tasks unfinished.", role=self.profile, send_to="User")
                
        return Message(content="Unknown task, idling.")
        
    def _save_state(self):
        """Save the current state to a status file for recovery."""
        if not self.status_file_path:
            return
            
        state = {
            "task_queue": self.task_queue,
            "phase": self.phase,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(self.status_file_path, 'w') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)