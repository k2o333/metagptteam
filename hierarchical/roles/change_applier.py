# hierarchical/roles/change_applier.py
import sys
import json
from pathlib import Path
from typing import Any, Dict, List

# --- 路径设置 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
METAGPT_ROOT = PROJECT_ROOT.parent / "metagpt"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(METAGPT_ROOT))
# -----------------

from metagpt.schema import Message
from metagpt.logs import logger
from hierarchical.roles.base_role import HierarchicalBaseRole

class ChangeApplier(HierarchicalBaseRole):
    """
    ChangeApplier Role.
    Applies text changes to documents based on messages from other roles.
    """
    name: str = "ChangeApplier"
    profile: str = "Change Applier"
    goal: str = "Apply text changes to documents based on rewrite instructions."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch(["ChangeApplicationRequest"])
        self.document_content = None
        self.document_path = None
        
    async def _think(self) -> bool:
        """
        Determines if there's a change application request to process.
        """
        if not self.rc.news:
            return False
            
        latest_msg = self.rc.news[-1]
        
        if latest_msg.cause_by == "ChangeApplicationRequest":
            logger.debug(f"ChangeApplier thinking: Found change application request. TODO set to the message itself.")
            self.rc.todo = "APPLY_CHANGE"
            return True
        
        logger.debug(f"ChangeApplier thinking: Latest message is not a change application request. No action needed.")
        return False

    def _apply_text_change(self, document_content: str, new_text: str, location_info: Dict[str, int]) -> str:
        """
        Apply a text change to the document content based on location information.
        
        Args:
            document_content: The full document content as a string
            new_text: The new text to insert
            location_info: Dictionary with start_line, start_char, end_line, end_char (0-based indices)
            
        Returns:
            The modified document content
        """
        lines = document_content.splitlines(keepends=True)
        
        start_line = location_info.get("start_line", 0)
        start_char = location_info.get("start_char", 0)
        end_line = location_info.get("end_line", 0)
        end_char = location_info.get("end_char", 0)
        
        # Validate indices
        if start_line < 0 or start_line >= len(lines) or end_line < 0 or end_line >= len(lines):
            logger.error(f"Invalid line indices: start_line={start_line}, end_line={end_line}, total_lines={len(lines)}")
            return document_content
            
        if start_char < 0 or start_char > len(lines[start_line]) or end_char < 0 or end_char > len(lines[end_line]):
            logger.error(f"Invalid character indices: start_char={start_char}, end_char={end_char}")
            return document_content
            
        # Handle same line replacement
        if start_line == end_line:
            line = lines[start_line]
            new_line = line[:start_char] + new_text + line[end_char:]
            lines[start_line] = new_line
        else:
            # Multi-line replacement
            # Replace start line from start_char onwards
            start_line_content = lines[start_line][:start_char]
            
            # Replace end line up to end_char
            end_line_content = lines[end_line][end_char:]
            
            # Combine with new text
            combined = start_line_content + new_text + end_line_content
            
            # Replace the lines in the array
            lines[start_line] = combined
            # Remove the lines in between (including the end line)
            del lines[start_line + 1:end_line + 1]
        
        return "".join(lines)

    async def _act(self) -> Message:
        logger.info(f"--- {self.name} is acting... ---")
        
        # Always call _think first
        await self._think()
        
        if self.rc.todo != "APPLY_CHANGE":
            logger.warning("ChangeApplier activated but todo is not a change application request. Skipping.")
            return None
            
        latest_msg = self.rc.news[-1]
            
        try:
            content_data = json.loads(latest_msg.content)
            new_text = content_data.get("new_text")
            location_info = content_data.get("location_info")
            document_path = content_data.get("document_path")
            
            if not new_text or not location_info or not document_path:
                logger.error("Missing required data in change application request.")
                return Message(content="Error: Missing required data in change application request.", role=self.profile, send_to="ChangeCoordinator")
            
            # Read the current document content
            doc_path = Path(document_path)
            if not doc_path.exists():
                logger.error(f"Document file not found: {document_path}")
                return Message(content=f"Error: Document file not found: {document_path}", role=self.profile, send_to="ChangeCoordinator")
                
            document_content = doc_path.read_text(encoding='utf-8')
            
            # Apply the change
            modified_content = self._apply_text_change(document_content, new_text, location_info)
            
            # Write back to file
            doc_path.write_text(modified_content, encoding='utf-8')
            
            logger.success(f"Successfully applied change to document: {document_path}")
            
            # Send completion message back to ChangeCoordinator
            completion_message = Message(
                content="Change applied successfully.",
                role=self.profile,
                send_to="ChangeCoordinator",
                cause_by="ChangeApplicationCompleted"
            )
            self.rc.env.publish_message(completion_message)
            
            return Message(content="Change applied successfully.", role=self.profile, send_to="ChangeCoordinator")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse change application request: {e}")
            return Message(content=f"Error: Failed to parse change application request: {e}", role=self.profile, send_to="ChangeCoordinator")
        except Exception as e:
            logger.error(f"Failed to apply change: {e}")
            return Message(content=f"Error: Failed to apply change: {e}", role=self.profile, send_to="ChangeCoordinator")