
import os
import json
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt_doc_writer.schemas.doc_structures import FinalDelivery

class Archiver(Role):
    def __init__(self, name="Archiver", profile="Archiver", goal="Archive the project deliverables", **kwargs):
        super().__init__(name, profile, goal, **kwargs)
        self.set_actions([]) # Non-LLM role
        self._watch({FinalDelivery}) # Watches for the final delivery message

    async def _act(self) -> Message:
        final_delivery_msg = self.rc.memory.get_by_class(FinalDelivery)[-1]
        archive_path = self._archive(final_delivery_msg.instruct_content)
        return Message(content=f"Project archived to {archive_path}")

    def _archive(self, final_delivery: FinalDelivery):
        archive_dir = "archive"
        os.makedirs(archive_dir, exist_ok=True)
        # In a real implementation, you would copy the final document and other artifacts.
        # For this example, we'll just write a dummy file.
        archive_file_path = os.path.join(archive_dir, "archive_summary.json")
        with open(archive_file_path, "w") as f:
            json.dump(final_delivery.dict(), f, indent=4)
        return archive_dir
