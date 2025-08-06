import sys
import json
from pathlib import Path
from typing import Any, Dict, List

# --- Path Setup ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
# -----------------

from metagpt.schema import Message
from metagpt.logs import logger
from hierarchical.roles.base_role import HierarchicalBaseRole
from metagpt.tools.libs.editor import Editor
from metagpt.tools.libs.linter import Linter


class SectionApplier(HierarchicalBaseRole):
    """
    SectionApplier Role.
    Applies section changes to Markdown documents based on messages from other roles.
    Uses Editor tool for precise file operations and Linter for validation.
    """
    name: str = "SectionApplier"
    profile: str = "Section Applier"
    goal: str = "Apply section changes to Markdown documents with validation."
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch(["SectionApplicationRequest"])
        self.editor = Editor()
        self.linter = Linter()
        
    async def _think(self) -> bool:
        """
        Determines if there's a section application request to process.
        """
        if not self.rc.news:
            return False
            
        latest_msg = self.rc.news[-1]
        
        if latest_msg.cause_by == "SectionApplicationRequest":
            logger.debug(f"SectionApplier thinking: Found section application request. TODO set to the message itself.")
            self.rc.todo = "APPLY_SECTION"
            return True
        
        logger.debug(f"SectionApplier thinking: Latest message is not a section application request. No action needed.")
        return False
        
    async def _act(self) -> Message:
        logger.info(f"--- {self.name} is acting... ---")
        
        # Always call _think first
        await self._think()
        
        if self.rc.todo != "APPLY_SECTION":
            logger.warning("SectionApplier activated but todo is not a section application request. Skipping.")
            return None
            
        latest_msg = self.rc.news[-1]
            
        try:
            content_data = json.loads(latest_msg.content)
            target_heading_string = content_data.get("target_heading_string")
            new_heading_and_content = content_data.get("new_heading_and_content")
            file_path = content_data.get("file_path")
            
            if not target_heading_string or not new_heading_and_content or not file_path:
                logger.error("Missing required data in section application request.")
                error_msg = "Error: Missing required data in section application request."
                self._send_completion_message(error_msg, "failed", target_heading_string, file_path)
                return Message(content=error_msg, role=self.profile, send_to="ChangeCoordinator")
            
            # Read the current document content
            doc_path = Path(file_path)
            if not doc_path.exists():
                logger.error(f"Document file not found: {file_path}")
                error_msg = f"Error: Document file not found: {file_path}"
                self._send_completion_message(error_msg, "failed", target_heading_string, file_path)
                return Message(content=error_msg, role=self.profile, send_to="ChangeCoordinator")
                
            document_content = doc_path.read_text(encoding='utf-8')
            
            # Find the target heading in the document
            heading_start_pos = document_content.find(target_heading_string)
            if heading_start_pos == -1:
                logger.error(f"Target heading not found in document: {target_heading_string}")
                error_msg = f"Error: Target heading not found in document: {target_heading_string}"
                self._send_completion_message(error_msg, "failed", target_heading_string, file_path)
                return Message(content=error_msg, role=self.profile, send_to="ChangeCoordinator")
                
            # Find the end of the current section (next heading or end of document)
            next_heading_pos = document_content.find("\n#", heading_start_pos + len(target_heading_string))
            if next_heading_pos == -1:
                section_end_pos = len(document_content)
            else:
                section_end_pos = next_heading_pos
                
            # Extract the current section content (including the heading)
            current_section = document_content[heading_start_pos:section_end_pos]
            
            # Apply the change using Editor tool
            try:
                # Use edit_file_by_replace to replace the entire section
                result = self.editor.edit_file_by_replace(
                    file_name=str(doc_path),
                    first_replaced_line_number=self._get_line_number(document_content, heading_start_pos),
                    first_replaced_line_content=current_section.split('\n')[0],
                    last_replaced_line_number=self._get_line_number(document_content, section_end_pos - 1),
                    last_replaced_line_content=current_section.split('\n')[-2] if section_end_pos > heading_start_pos and '\n' in current_section else current_section.split('\n')[-1],
                    new_content=new_heading_and_content
                )
                logger.info(f"Successfully applied section change using Editor tool: {result}")
            except ValueError as e:
                logger.error(f"Editor tool validation failed: {e}")
                error_msg = f"Error: Editor tool validation failed: {e}"
                self._send_completion_message(error_msg, "failed", target_heading_string, file_path)
                return Message(content=error_msg, role=self.profile, send_to="ChangeCoordinator")
                
            # Validate the modified file with Linter
            try:
                lint_result = self.linter.lint(str(doc_path))
                if lint_result:
                    logger.warning(f"Linter found issues: {lint_result.text}")
                    # For Markdown files, we might want to be more lenient
                    # But we still report the issues
            except Exception as e:
                logger.warning(f"Linter validation encountered an error (continuing): {e}")
                
            logger.success(f"Successfully applied section change to document: {file_path}")
            
            # Send completion message back to ChangeCoordinator
            success_msg = f"Section '{target_heading_string}' applied successfully."
            self._send_completion_message(success_msg, "success", target_heading_string, file_path)
            
            return Message(content=success_msg, role=self.profile, send_to="ChangeCoordinator")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse section application request: {e}")
            error_msg = f"Error: Failed to parse section application request: {e}"
            self._send_completion_message(error_msg, "failed", "", "")
            return Message(content=error_msg, role=self.profile, send_to="ChangeCoordinator")
        except Exception as e:
            logger.error(f"Failed to apply section change: {e}")
            error_msg = f"Error: Failed to apply section change: {e}"
            self._send_completion_message(error_msg, "failed", "", "")
            return Message(content=error_msg, role=self.profile, send_to="ChangeCoordinator")
            
    def _get_line_number(self, content: str, pos: int) -> int:
        """Get the 1-based line number for a position in the content."""
        return content[:pos].count('\n') + 1
        
    def _send_completion_message(self, message: str, status: str, applied_heading: str, file_path: str):
        """Send a completion message to the environment."""
        completion_message = Message(
            content=json.dumps({
                "status": status,
                "message": message,
                "applied_heading": applied_heading,
                "file_path": file_path
            }),
            role=self.profile,
            send_to="ChangeCoordinator",
            cause_by="SectionApplicationCompleted"
        )
        self.rc.env.publish_message(completion_message)