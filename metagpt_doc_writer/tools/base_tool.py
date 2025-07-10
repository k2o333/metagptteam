
from abc import ABC, abstractmethod
from pydantic import BaseModel

class ToolSchema(BaseModel):
    """Pydantic model for describing a tool's interface."""
    name: str
    description: str
    parameters: type[BaseModel]

class BaseTool(ABC):
    """Abstract base class for all tools."""
    
    @property
    @abstractmethod
    def schema(self) -> ToolSchema:
        """Returns the schema describing the tool."""
        ...
        
    @abstractmethod
    async def run(self, **kwargs) -> str:
        """Executes the tool with the given parameters."""
        ...

    def get_description(self) -> str:
        # This can be enhanced to generate a more detailed description from the schema
        return f"{self.schema.name} - {self.schema.description}"
