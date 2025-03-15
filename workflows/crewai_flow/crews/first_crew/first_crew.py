import os
from typing import List, Dict, Any
from pydantic import BaseModel, Field

"""
Data Analysis Crew for CrewAI Flow

Cursor Rules for AI Agents:
---------------------------
1. Output Format: The output from this crew can be formatted in two ways:
   - 'markdown': Human-readable format with headers and formatting (default in Kodosumi UI)
   - 'json': Machine-readable format for agent-to-agent interactions
   
   AI agents should request 'json' format when programmatically processing the results.

2. Output Structure: The output follows the FirstCrewOutput model structure with:
   - summary: A text summary of the analysis
   - insights: A list of key insights discovered
   - recommendations: A list of actionable recommendations

3. Integration: When calling this crew directly, the raw output will be in the format
   specified by the flow's output_format parameter.
"""

from crewai import Agent, Crew, Process, Task
from langchain_openai import ChatOpenAI

# Define your output model
class FirstCrewOutput(BaseModel):
    """
    Output model for the DataAnalysisCrew
    
    This model defines the structure of the output from the crew.
    The output can be formatted as either markdown (human-readable) or
    JSON (for agent-to-agent interactions) based on the flow's output_format parameter.
    """
    summary: str = Field(..., description="Summary of the data analysis")
    insights: List[str] = Field(..., description="Key insights from the analysis")
    recommendations: List[str] = Field(..., description="Recommendations based on the analysis")

class FirstCrew:
    """
    Data Analysis Crew.
    This crew analyzes data and provides insights and recommendations.
    """
    
    def __init__(self):
        """Initialize the crew with any necessary configuration"""
        # Initialize your LLM
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.2,
            api_key=api_key
        )
    
    def crew(self) -> Crew:
        """
        Create and return the crew.
        This method is called by the flow to get the crew.
        """
        # Create agents
        data_analyst = Agent(
            name="Data Analyst",
            role="Senior Data Analyst",
            goal="Analyze data and extract meaningful patterns",
            backstory="You are an experienced data analyst with expertise in finding patterns and insights in various types of data.",
            llm=self.llm,
            verbose=True
        )
        
        insights_specialist = Agent(
            name="Insights Specialist",
            role="Business Insights Specialist",
            goal="Convert data analysis into actionable business insights",
            backstory="You specialize in translating technical data findings into business insights and recommendations that can drive decision-making.",
            llm=self.llm,
            verbose=True
        )
        
        # Create tasks
        analysis_task = Task(
            name="Analyze Data",
            agent=data_analyst,
            description="""
            Analyze the following data and identify key patterns and trends:
            
            Dataset: {dataset_name}
            Description: {dataset_description}
            Sample data points: {sample_data}
            
            Provide a detailed analysis of the patterns and trends you observe.
            """,
            expected_output="A detailed analysis of the data with identified patterns and trends"
        )
        
        insights_task = Task(
            name="Generate Insights and Recommendations",
            agent=insights_specialist,
            description="""
            Based on the data analysis provided, generate business insights and actionable recommendations.
            
            Analysis: {analysis_result}
            
            Provide:
            1. A summary of the analysis
            2. Key business insights
            3. Actionable recommendations
            """,
            context=[analysis_task],
            expected_output="Business insights and actionable recommendations based on the data analysis"
        )
        
        # Create and return the crew
        return Crew(
            agents=[data_analyst, insights_specialist],
            tasks=[analysis_task, insights_task],
            process=Process.sequential,
            verbose=True
        ) 