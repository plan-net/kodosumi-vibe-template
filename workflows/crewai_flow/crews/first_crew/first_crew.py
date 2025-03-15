from typing import List, Dict, Any
from pydantic import BaseModel, Field

from crewai import Agent, Crew, Process, Task
from langchain_openai import ChatOpenAI

# Define your output model
class FirstCrewOutput(BaseModel):
    """Output model for the FirstCrew"""
    result: str = Field(..., description="The result of the crew's work")
    details: Dict[str, Any] = Field(..., description="Additional details about the result")

class FirstCrew:
    """
    First crew in the flow.
    This crew is responsible for the first step in the flow.
    """
    
    def __init__(self):
        """Initialize the crew with any necessary configuration"""
        # Initialize your LLM
        self.llm = ChatOpenAI()
    
    def crew(self) -> Crew:
        """
        Create and return the crew.
        This method is called by the flow to get the crew.
        """
        # Create agents
        agent1 = Agent(
            name="Agent 1",
            role="Role of Agent 1",
            goal="Goal of Agent 1",
            backstory="Backstory of Agent 1",
            llm=self.llm,
            verbose=True
        )
        
        agent2 = Agent(
            name="Agent 2",
            role="Role of Agent 2",
            goal="Goal of Agent 2",
            backstory="Backstory of Agent 2",
            llm=self.llm,
            verbose=True
        )
        
        # Create tasks
        task1 = Task(
            name="Task 1",
            agent=agent1,
            description="Description of Task 1. Uses input parameters: {param1}, {param2}",
            expected_output="Expected output of Task 1"
        )
        
        task2 = Task(
            name="Task 2",
            agent=agent2,
            description="Description of Task 2. Uses the output of Task 1.",
            context=[task1],
            expected_output="Expected output of Task 2"
        )
        
        # Create and return the crew
        return Crew(
            agents=[agent1, agent2],
            tasks=[task1, task2],
            process=Process.sequential,
            verbose=True
        ) 