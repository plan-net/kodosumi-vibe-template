import os
import yaml
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, output_pydantic, before_kickoff, after_kickoff
from langchain_openai import ChatOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    agents_config_path = 'config/agents.yaml'
    tasks_config_path = 'config/tasks.yaml'
    
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
        
        # Load configurations
        self.agents_config = self._load_config(self.agents_config_path)
        self.tasks_config = self._load_config(self.tasks_config_path)
        
        logger.info(f"Loaded agent configs: {list(self.agents_config.keys()) if self.agents_config else 'None'}")
        logger.info(f"Loaded task configs: {list(self.tasks_config.keys()) if self.tasks_config else 'None'}")
    
    def _load_config(self, config_path):
        """
        Load configuration from a YAML file
        
        Args:
            config_path: Path to the YAML file
            
        Returns:
            dict: Configuration from the YAML file
        """
        try:
            # Get the absolute path to the config file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(current_dir, config_path)
            
            logger.info(f"Loading config from: {full_path}")
            
            if not os.path.exists(full_path):
                logger.warning(f"Config file not found at {full_path}")
                return {}
                
            with open(full_path, 'r') as f:
                config = yaml.safe_load(f)
                
            return config
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            return {}
    
    @output_pydantic
    def data_analysis_output(self) -> DataAnalysisOutput:
        """Register the DataAnalysisOutput model with CrewBase"""
        return DataAnalysisOutput
    
    @output_pydantic
    def business_insights_output(self) -> BusinessInsightsOutput:
        """Register the BusinessInsightsOutput model with CrewBase"""
        return BusinessInsightsOutput
    
    @agent
    def data_analyst(self) -> Agent:
        """
        Create the data analyst agent
        """
        try:
            if 'data_analyst' not in self.agents_config:
                logger.warning("data_analyst not found in agents_config")
                # Provide default configuration
                config = {
                    "name": "Data Analyst",
                    "role": "Senior Data Analyst",
                    "goal": "Analyze data and extract meaningful patterns",
                    "backstory": "You are an experienced data analyst with expertise in finding patterns and insights in various types of data."
                }
            else:
                config = self.agents_config['data_analyst']
                
            return Agent(
                config=config,
                llm=self.llm,
                verbose=True
            )
        except Exception as e:
            logger.error(f"Error creating data_analyst agent: {e}")
            raise
    
    @agent
    def insights_specialist(self) -> Agent:
        """
        Create the insights specialist agent
        """
        try:
            if 'insights_specialist' not in self.agents_config:
                logger.warning("insights_specialist not found in agents_config")
                # Provide default configuration
                config = {
                    "name": "Insights Specialist",
                    "role": "Business Insights Specialist",
                    "goal": "Convert data analysis into actionable business insights",
                    "backstory": "You specialize in translating technical data findings into business insights and recommendations that can drive decision-making."
                }
            else:
                config = self.agents_config['insights_specialist']
                
            return Agent(
                config=config,
                llm=self.llm,
                verbose=True
            )
        except Exception as e:
            logger.error(f"Error creating insights_specialist agent: {e}")
            raise
    
    @task
    def analyze_data_task(self) -> Task:
        """
        Create the data analysis task
        """
        try:
            if 'analyze_data' not in self.tasks_config:
                logger.warning("analyze_data not found in tasks_config")
                # Provide default configuration
                task_config = {
                    "name": "Analyze Data",
                    "description": "Analyze the dataset and identify key patterns and trends."
                }
            else:
                task_config = dict(self.tasks_config['analyze_data'])
                
            logger.info(f"Creating analyze_data_task with config: {task_config}")
            
            # Set the output_pydantic class
            return Task(
                config=task_config,
                agent=self.data_analyst(),
                output_pydantic=DataAnalysisOutput
            )
        except Exception as e:
            logger.error(f"Error creating analyze_data_task: {e}")
            raise
    
    @task
    def generate_insights_task(self) -> Task:
        """
        Create the insights generation task
        """
        try:
            if 'generate_insights' not in self.tasks_config:
                logger.warning("generate_insights not found in tasks_config")
                # Provide default configuration
                task_config = {
                    "name": "Generate Insights and Recommendations",
                    "description": "Based on the data analysis, generate business insights and actionable recommendations."
                }
            else:
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
                
            logger.info(f"Creating generate_insights_task with config: {task_config}")
            
            return Task(
                config=task_config,
                agent=self.insights_specialist(),
                context=[self.analyze_data_task()],
                output_pydantic=BusinessInsightsOutput
            )
        except Exception as e:
            logger.error(f"Error creating generate_insights_task: {e}")
            raise
    
    @crew
    def crew(self) -> Crew:
        """
        Create and return the crew.
        This method is called by the flow to get the crew.
        
        Returns:
            Crew: A configured CrewAI crew for data analysis
        """
        try:
            logger.info("Creating crew with agents and tasks")
            return Crew(
                agents=self.agents,
                tasks=self.tasks,
                process=Process.sequential,
                verbose=True
            )
        except Exception as e:
            logger.error(f"Error creating crew: {e}")
            raise 