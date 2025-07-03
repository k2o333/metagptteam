
import os
import json
import shutil
from pathlib import Path
from datetime import datetime

from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team
from metagpt.logs import logger

from metagpt_doc_writer.schemas.doc_structures import FinalDelivery, ProjectArchived

class Archiver(Role):
    """
    A non-LLM role responsible for archiving the project's final deliverables,
    performance reports, and a snapshot of the team's state for future reference.
    """
    def __init__(self, name="Archiver", profile="Archiver", goal="Archive project deliverables", archive_path: str = "./archive", **kwargs):
        super().__init__(name, profile, goal, **kwargs)
        self.set_actions([])  # Non-LLM role
        self._watch({FinalDelivery})  # Watches for the final delivery message
        self.archive_path = Path(archive_path)

    async def _act(self) -> Message:
        """The main action for the Archiver role."""
        logger.info("Archiver received FinalDelivery, starting archiving process...")
        final_delivery_msg = self.rc.memory.get_by_class(FinalDelivery)[-1]
        
        # Create a unique directory for this project archive
        project_name = self.rc.memory.get_by_class(Message)[0].content # Crude way to get project idea
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_dir = self.archive_path / f"{project_name.replace(' ', '_')}_{timestamp}"
        archive_dir.mkdir(parents=True, exist_ok=True)

        # 1. Archive final deliverables
        self._archive_deliverables(final_delivery_msg.instruct_content, archive_dir)

        # 2. Archive performance report
        self._archive_performance_report(archive_dir)

        # 3. Archive team state snapshot
        self._archive_team_state(archive_dir)

        logger.info(f"Project successfully archived to {archive_dir}")
        return Message(content=f"Project archived to {archive_dir}", instruct_content=ProjectArchived(archive_path=str(archive_dir)))

    def _archive_deliverables(self, final_delivery: FinalDelivery, archive_dir: Path):
        """Copies the final documents to the archive directory."""
        logger.info("Archiving final deliverables...")
        for file_path_str in final_delivery.file_paths:
            file_path = Path(file_path_str)
            if file_path.exists():
                shutil.copy(file_path, archive_dir / file_path.name)
            else:
                logger.warning(f"Could not find deliverable file to archive: {file_path_str}")

    def _archive_performance_report(self, archive_dir: Path):
        """Finds the performance report and copies it to the archive directory."""
        logger.info("Archiving performance report...")
        # Assumes report is in a standard location, e.g., the project root
        performance_report_path = Path("performance_report.json")
        if performance_report_path.exists():
            shutil.copy(performance_report_path, archive_dir / performance_report_path.name)
        else:
            logger.warning("Performance report not found, skipping archiving.")

    def _archive_team_state(self, archive_dir: Path):
        """Serializes the entire team state for future recovery or analysis."""
        logger.info("Archiving team state...")
        if self.rc.env and isinstance(self.rc.env.team, Team):
            try:
                self.rc.env.team.serialize(archive_dir / "team_snapshot.json")
            except Exception as e:
                logger.error(f"Failed to serialize team state: {e}")
        else:
            logger.warning("Team object not found in environment, cannot archive state.")
