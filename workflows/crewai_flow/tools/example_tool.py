from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type

class ExampleToolInput(BaseModel):
    """Input for the ExampleTool"""
    query: str = Field(..., description="The query to process")

class ExampleTool(BaseTool):
    """
    An example tool for the CrewAI flow.
    This tool demonstrates how to create a custom tool for CrewAI.
    """
    name: str = "example_tool"
    description: str = "A tool that processes a query and returns a result"
    args_schema: Type[BaseModel] = ExampleToolInput
    
    def _run(self, query: str) -> str:
        """
        Run the tool.
        This method is called when the tool is used.
        """
        # Add your tool logic here
        return f"Processed query: {query}"
    
    async def _arun(self, query: str) -> str:
        """
        Run the tool asynchronously.
        This method is called when the tool is used asynchronously.
        """
        # Add your async tool logic here
        return self._run(query) 