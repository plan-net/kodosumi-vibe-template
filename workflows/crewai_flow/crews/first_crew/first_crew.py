import os
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff
from langchain_openai import ChatOpenAI

# Define Pydantic models for task outputs
class DataAnalysisOutput(BaseModel):
    """
    Output model for the data analysis task.
    This defines the structure of the output from the data analysis task.
    """
    patterns: List[str] = Field(..., description="List of identified patterns in the data")
    trends: List[str] = Field(..., description="List of identified trends in the data")
    analysis: str = Field(..., description="Detailed analysis of the data")

class BusinessInsightsOutput(BaseModel):
    """
    Output model for the business insights task.
    This defines the structure of the output from the business insights task.
    """
    summary: str = Field(..., description="Summary of the data analysis")
    insights: List[str] = Field(..., description="Key insights from the analysis")
    recommendations: List[str] = Field(..., description="Recommendations based on the analysis")

@CrewBase
class FirstCrew:
    """
    Data Analysis Crew.
    This crew analyzes data and provides insights and recommendations.
    
    Following the recommended patterns from the crews rule:
    - Uses sequential processes by default
    - Loads agent and task configurations from YAML files
    - Uses output_pydantic for structured output
    """
    
    # Paths to YAML configuration files
    agents_config = 'crews/first_crew/config/agents.yaml'
    tasks_config = 'crews/first_crew/config/tasks.yaml'
    
    def __init__(self):
        """
        Initialize the crew with any necessary configuration
        """
        super().__init__()
        
        # Initialize the LLM
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
            
        # Use the OpenAI LLM
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.2,
            api_key=api_key
        )
    
    @agent
    def data_analyst(self) -> Agent:
        """
        Create the data analyst agent
        """
        return Agent(
            config=self.agents_config['data_analyst'],
            llm=self.llm,
            verbose=True
        )
    
    @agent
    def insights_specialist(self) -> Agent:
        """
        Create the insights specialist agent
        """
        return Agent(
            config=self.agents_config['insights_specialist'],
            llm=self.llm,
            verbose=True
        )
    
    @task
    def analyze_data_task(self) -> Task:
        """
        Create the data analysis task
        """
        task_config = dict(self.tasks_config['analyze_data'])
        
        # Set the output_pydantic class
        return Task(
            config=task_config,
            agent=self.data_analyst,
            output_pydantic=DataAnalysisOutput
        )
    
    @task
    def generate_insights_task(self) -> Task:
        """
        Create the insights generation task
        """
        # Get the base configuration
        task_config = dict(self.tasks_config['generate_insights'])
        
        # Add instructions to help the agent structure the output correctly
        instruction = """
        
        IMPORTANT: Structure your response to include:
        - A concise summary of the analysis
        - A list of key business insights
        - A list of actionable recommendations
        
        This will help ensure your output can be properly processed.
        """
        
        # Append instructions to the description
        if 'description' in task_config:
            task_config['description'] += instruction
        
        return Task(
            config=task_config,
            agent=self.insights_specialist,
            context=[self.analyze_data_task],
            output_pydantic=BusinessInsightsOutput
        )
    
    @crew
    def crew(self) -> Crew:
        """
        Create and return the crew.
        This method is called by the flow to get the crew.
        
        Returns:
            Crew: A configured CrewAI crew for data analysis
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        ) 