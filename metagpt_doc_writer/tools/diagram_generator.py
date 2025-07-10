# /root/metagpt/mgfr/metagpt_doc_writer/tools/diagram_generator.py

from pydantic import BaseModel, Field
from .base_tool import BaseTool, ToolSchema

class DiagramGeneratorParams(BaseModel):
    """Parameters for the diagram generator tool."""
    diagram_type: str = Field(..., description="Type of the diagram, e.g., 'sequence', 'class'")
    content: str = Field(..., description="The content or description to be converted into a diagram.")

class DiagramGenerator(BaseTool):
    """
    A tool to generate diagram code (e.g., Mermaid.js) from natural language descriptions.
    """
    
    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="diagram_generator",
            description="Generates diagram code (e.g., Mermaid.js) from a natural language description.",
            parameters=DiagramGeneratorParams,
        )

    async def run(self, diagram_type: str, content: str) -> str:
        """
        Executes the diagram generation tool.
        
        Args:
            diagram_type: The type of diagram to generate.
            content: The natural language description for the diagram.

        Returns:
            A string containing the generated diagram code in a markdown block.
        """
        # Placeholder implementation.
        # In a real scenario, this would call an LLM to generate Mermaid code based on the content.
        # For now, we return a simple, valid Mermaid code block as a placeholder.
        mermaid_code = f"""
graph TD;
    A[{diagram_type.capitalize()}] --> B{{'{content[:20]}...'}};
"""
        return f"```mermaid\n{mermaid_code}\n```"

    def get_description(self) -> str:
        """Generates a string representation for the LLM to understand."""
        # This can be auto-generated from the schema for more complex tools
        return "diagram_generator(diagram_type: str, content: str) - Generates diagram code (e.g., Mermaid.js) from a natural language description."