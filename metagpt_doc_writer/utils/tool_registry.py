# /root/metagpt/mgfr/metagpt_doc_writer/utils/tool_registry.py

from metagpt_doc_writer.tools.base_tool import BaseTool

class ToolRegistry:
    def __init__(self, tools: list[BaseTool]):
        # FIX: Access the tool's name via its schema property, i.e., tool.schema.name
        self._tools = {tool.schema.name: tool for tool in tools}

    def get_tool(self, name: str) -> BaseTool:
        return self._tools.get(name)

    def get_tools_description(self) -> str:
        """Generates a markdown formatted list of all available tools for the LLM prompt."""
        if not self._tools:
            return ""
        descriptions = [tool.get_description() for tool in self._tools.values()]
        return "## Available Tools\n" + "\n".join(f"- {d}" for d in descriptions)