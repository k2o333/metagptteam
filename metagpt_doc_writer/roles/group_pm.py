
from .base_role import MyBaseRole

class GroupPM(MyBaseRole):
    name: str = "GroupPM"
    profile: str = "Group Product Manager"
    goal: str = "Break down high-level tasks into smaller, manageable parts"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # This role will likely have actions to create module outlines
        # For now, we'll leave it as a placeholder
