import os
import json
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, after_kickoff, agent, before_kickoff, crew, task
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, validator

from workflows.common.logging_utils import get_logger, log_errors
from workflows.tools.exa_search.tool import ExaSearchTool

# Set up logger
logger = get_logger(__name__)


# Define validation functions for guardrails
def validate_research_output(task_output: Any) -> Tuple[bool, Union[Dict[str, Any], str]]:
    """
    Validate and parse the research output result.
    
    Args:
        task_output: The TaskOutput object from the agent
        
    Returns:
        A tuple of (is_valid, parsed_data_or_error_message)
    """
    try:
        # Get the raw output
        result = task_output.raw if hasattr(task_output, 'raw') else str(task_output)
        
        # Try to parse as JSON
        data = {}
        if hasattr(task_output, 'json_dict') and task_output.json_dict:
            data = task_output.json_dict
        else:
            try:
                data = json.loads(result)
            except json.JSONDecodeError as e:
                return (False, f"Invalid JSON format at line {e.lineno}, column {e.colno}")
        
        # Check for required fields
        if "summary" not in data:
            return (False, "Missing required field: summary")
        
        if len(data.get("summary", "").split()) < 100:
            return (False, "Summary is too short: provide a comprehensive summary with actionable insights")
        
        if "sources" not in data or not isinstance(data["sources"], list):
            return (False, "Missing or invalid sources field: must be a list")
            
        if len(data["sources"]) < 5:
            return (False, "Not enough sources: at least 5 highly relevant sources are required")
            
        if len(data["sources"]) > 15:
            return (False, "Too many sources: focus on 8-12 HIGHLY RELEVANT sources rather than quantity")
            
        # Check that each source has required fields
        for idx, source in enumerate(data["sources"]):
            if not isinstance(source, dict):
                return (False, f"Source at index {idx} is not a dictionary")
                
            # Check for required source fields
            for field in ["id", "title", "url", "summary"]:
                if field not in source:
                    return (False, f"Source at index {idx} is missing required field: {field}")
                    
            # Check for sufficient source summaries
            if len(source.get("summary", "").split()) < 30:
                return (False, f"Source {source.get('id', f'at index {idx}')} has an insufficient summary: provide at least 2-3 sentences with actionable insights")
                    
            # Ensure source ID is unique
            for i, other_source in enumerate(data["sources"]):
                if i != idx and other_source.get("id") == source.get("id"):
                    return (False, f"Duplicate source ID: {source.get('id')}")
        
        if "search_queries_used" not in data or not isinstance(data["search_queries_used"], list):
            return (False, "Missing or invalid search_queries_used field: must be a list")
            
        if len(data["search_queries_used"]) < 3:
            return (False, "Not enough search queries: at least 3 targeted search queries are required")
            
        # Check for targeted search queries that combine multiple elements
        for idx, query in enumerate(data.get("search_queries_used", [])):
            if len(query.split()) < 3:
                return (False, f"Search query at index {idx} is not targeted enough: '{query}'. Create targeted queries that combine multiple elements.")
        
        return (True, data)
    except Exception as e:
        return (False, f"Validation error: {str(e)}")

# Define Pydantic models for task outputs
class ResearchOutput(BaseModel):
    """
    Output model for the research task.
    This defines the structure of the output from the research task.
    
    Example:
    ```json
    {
        "summary": "BMW has been focusing on sustainable electric vehicle production...",
        "sources": [
            {
                "id": "S1",
                "title": "BMW Electric Vehicle Strategy 2025",
                "url": "https://www.example.com/bmw-strategy",
                "summary": "BMW plans to launch 12 fully electric models by 2025..."
            },
            {
                "id": "S2",
                "title": "Luxury EV Market Analysis",
                "url": "https://www.example.com/luxury-ev-market",
                "summary": "The luxury EV market is growing at 25% annually with environmentally conscious buyers..."
            }
        ],
        "search_queries_used": [
            "BMW electric vehicles marketing strategy",
            "environmentally conscious luxury car buyers preferences",
            "electric vehicle market share growth tactics"
        ]
    }
    ```
    """

    summary: str = Field(
        ..., 
        description="A comprehensive summary of all research findings with actionable insights",
        min_length=200,
        examples=["BMW's electric vehicle lineup has shown strong growth with environmentally conscious buyers..."]
    )
    
    sources: List[Dict[str, str]] = Field(
        ..., 
        description="List of 8-12 highly relevant sources used in the research",
        min_items=5,
        max_items=15,
        examples=[[
            {
                "id": "S1",
                "title": "BMW Electric Vehicle Strategy 2025",
                "url": "https://www.example.com/bmw-strategy",
                "summary": "BMW plans to launch 12 fully electric models by 2025 with a focus on sustainability..."
            }
        ]]
    )
    
    search_queries_used: List[str] = Field(
        ...,
        description="List of all search queries used to gather information (minimum 3)",
        min_items=3,
        examples=[["BMW electric vehicles marketing strategy", "luxury EV market trends 2024"]]
    )
    
    @validator('sources')
    def validate_sources(cls, sources):
        """Validate that each source has the required fields and unique IDs."""
        seen_ids = set()
        for i, source in enumerate(sources):
            # Check required fields
            for field in ["id", "title", "url", "summary"]:
                if field not in source:
                    raise ValueError(f"Source at index {i} is missing required field: {field}")
            
            # Check for sufficient summary length    
            if len(source.get("summary", "").split()) < 30:
                raise ValueError(f"Source {source.get('id')} has an insufficient summary: provide at least 2-3 sentences")
                
            # Check for duplicate IDs
            source_id = source.get("id")
            if source_id in seen_ids:
                raise ValueError(f"Duplicate source ID: {source_id}")
            seen_ids.add(source_id)
            
        return sources
        
    @validator('search_queries_used')
    def validate_search_queries(cls, queries):
        """Validate that search queries are specific enough."""
        for i, query in enumerate(queries):
            if len(query.split()) < 3:
                raise ValueError(f"Search query '{query}' is not specific enough: add more search terms")
        return queries


def validate_obvious_hypotheses_output(task_output: Any) -> Tuple[bool, Union[Dict[str, Any], str]]:
    """
    Validate and parse the obvious hypotheses output result.
    
    Args:
        task_output: The TaskOutput object from the agent
        
    Returns:
        A tuple of (is_valid, parsed_data_or_error_message)
    """
    try:
        # Get the raw output
        result = task_output.raw if hasattr(task_output, 'raw') else str(task_output)
        
        # Try to parse as JSON
        data = {}
        if hasattr(task_output, 'json_dict') and task_output.json_dict:
            data = task_output.json_dict
        else:
            try:
                data = json.loads(result)
            except json.JSONDecodeError as e:
                return (False, f"Invalid JSON format at line {e.lineno}, column {e.colno}")
        
        # Check for required fields
        if "hypotheses" not in data or not isinstance(data["hypotheses"], list):
            return (False, "Missing or invalid hypotheses field: must be a list")
            
        if len(data["hypotheses"]) < 3:
            return (False, "Not enough hypotheses: at least 3 hypotheses are required")
            
        # Check that each hypothesis has required fields
        for idx, hyp in enumerate(data["hypotheses"]):
            if not isinstance(hyp, dict):
                return (False, f"Hypothesis at index {idx} is not a dictionary")
                
            # Check for hypothesis text
            if "hypothesis" not in hyp or not hyp["hypothesis"]:
                return (False, f"Hypothesis at index {idx} is missing required field: hypothesis")
                
            # Check for rationale
            if "rationale" not in hyp or not hyp["rationale"]:
                return (False, f"Hypothesis at index {idx} is missing required field: rationale")
                
            # Check for sources
            if "sources" not in hyp or not hyp["sources"]:
                return (False, f"Hypothesis at index {idx} is missing source references")
                
            if not isinstance(hyp["sources"], list):
                return (False, f"Hypothesis {idx+1} sources must be a list of source IDs")
                
            if len(hyp["sources"]) < 1:
                return (False, f"Hypothesis at index {idx} must cite at least one source")
        
        return (True, data)
    except Exception as e:
        return (False, f"Validation error: {str(e)}")

class ObviousHypothesesOutput(BaseModel):
    """
    Output model for the obvious hypotheses generation task.
    
    Example:
    ```json
    {
        "hypotheses": [
            {
                "hypothesis": "If we highlight BMW's sustainable manufacturing processes in marketing campaigns, then environmentally conscious luxury car buyers will be more likely to purchase BMW electric vehicles over competitors",
                "rationale": "Environmentally conscious consumers care deeply about the complete lifecycle environmental impact of their purchases. BMW's carbon-neutral factory in Leipzig is a competitive advantage that resonates with this audience and differentiates the brand from competitors who only focus on zero emissions during vehicle use.",
                "sources": ["S1", "S3", "S7"]
            },
            {
                "hypothesis": "If we emphasize the premium interior materials made from recycled sources, then environmentally conscious luxury car buyers will perceive greater alignment between luxury and sustainability values",
                "rationale": "Research shows that environmentally conscious luxury consumers often experience cognitive dissonance between luxury consumption and environmental values. By highlighting how BMW resolves this tension through sustainable luxury materials, we directly address this psychological barrier to purchase.",
                "sources": ["S2", "S5"]
            }
        ]
    }
    ```
    """

    hypotheses: List[Dict[str, Any]] = Field(
        ...,
        description="List of 5-10 obvious marketing hypotheses with supporting rationale and source references",
        min_items=3,
        max_items=10,
        examples=[[
            {
                "hypothesis": "If we highlight BMW's sustainable manufacturing processes in marketing campaigns, then environmentally conscious luxury car buyers will be more likely to purchase BMW electric vehicles over competitors",
                "rationale": "Environmentally conscious consumers care deeply about the complete lifecycle environmental impact of their purchases. BMW's carbon-neutral factory in Leipzig is a competitive advantage that resonates with this audience.",
                "sources": ["S1", "S3", "S7"]
            }
        ]]
    )
    
    @validator('hypotheses')
    def validate_source_references(cls, hypotheses):
        """Validate that each hypothesis has the required fields and properly formatted sources."""
        for i, hyp in enumerate(hypotheses):
            # Check for required fields
            if "hypothesis" not in hyp or not hyp["hypothesis"]:
                raise ValueError(f"Hypothesis {i+1} is missing required field: hypothesis")
                
            # Validate hypothesis format
            hypothesis_text = hyp.get("hypothesis", "")
            if not ("If we" in hypothesis_text and "then" in hypothesis_text):
                raise ValueError(f"Hypothesis {i+1} must follow the format: 'If we [action], then [target audience] will [desired outcome]'")
            
            # Check for rationale
            if "rationale" not in hyp or not hyp["rationale"]:
                raise ValueError(f"Hypothesis {i+1} is missing required field: rationale")
                
            # Check rationale length
            if len(hyp.get("rationale", "").split()) < 20:
                raise ValueError(f"Hypothesis {i+1} has insufficient rationale: provide at least 2-3 sentences")
                
            # Check for sources
            if "sources" not in hyp or not hyp["sources"]:
                raise ValueError(f"Hypothesis {i+1} is missing source references")
                
            if not isinstance(hyp["sources"], list):
                raise ValueError(f"Hypothesis {i+1} sources must be a list of source IDs")
                
            if len(hyp["sources"]) < 1:
                raise ValueError(f"Hypothesis {i+1} must cite at least one source")
                
        return hypotheses


def validate_innovative_hypotheses_output(task_output: Any) -> Tuple[bool, Union[Dict[str, Any], str]]:
    """
    Validate and parse the innovative hypotheses output result.
    
    Args:
        task_output: The TaskOutput object from the agent
        
    Returns:
        A tuple of (is_valid, parsed_data_or_error_message)
    """
    try:
        # Get the raw output
        result = task_output.raw if hasattr(task_output, 'raw') else str(task_output)
        
        # Try to parse as JSON
        data = {}
        if hasattr(task_output, 'json_dict') and task_output.json_dict:
            data = task_output.json_dict
        else:
            try:
                data = json.loads(result)
            except json.JSONDecodeError as e:
                return (False, f"Invalid JSON format at line {e.lineno}, column {e.colno}")
        
        # Check for required fields
        if "hypotheses" not in data or not isinstance(data["hypotheses"], list):
            return (False, "Missing or invalid hypotheses field: must be a list")
            
        if len(data["hypotheses"]) < 3:
            return (False, "Not enough hypotheses: at least 3 innovative hypotheses are required")
            
        # Check that each hypothesis has required fields
        for idx, hyp in enumerate(data["hypotheses"]):
            if not isinstance(hyp, dict):
                return (False, f"Hypothesis at index {idx} is not a dictionary")
                
            # Check for hypothesis text
            if "hypothesis" not in hyp or not hyp["hypothesis"]:
                return (False, f"Hypothesis at index {idx} is missing required field: hypothesis")
                
            # Check for rationale
            if "rationale" not in hyp or not hyp["rationale"]:
                return (False, f"Hypothesis at index {idx} is missing required field: rationale")
                
            # Check for difference (unique to innovative hypotheses)
            if "difference" not in hyp or not hyp["difference"]:
                return (False, f"Hypothesis at index {idx} is missing required field: difference")
                
            # Check for sources
            if "sources" not in hyp or not hyp["sources"]:
                return (False, f"Hypothesis at index {idx} is missing source references")
                
            if not isinstance(hyp["sources"], list):
                return (False, f"Hypothesis {idx+1} sources must be a list of source IDs")
                
            if len(hyp["sources"]) < 1:
                return (False, f"Hypothesis at index {idx} must cite at least one source")
        
        return (True, data)
    except Exception as e:
        return (False, f"Validation error: {str(e)}")

class InnovativeHypothesesOutput(BaseModel):
    """
    Output model for the innovative hypotheses generation task.
    
    Example:
    ```json
    {
        "hypotheses": [
            {
                "hypothesis": "If we create exclusive 'carbon offset credits' that BMW EV buyers can gift to others, then environmentally conscious luxury car buyers will become brand ambassadors who expand our reach beyond direct marketing",
                "rationale": "Research shows that environmentally conscious consumers value the ability to influence others' behavior. By enabling BMW EV buyers to gift tangible environmental benefits to friends and family, we turn customers into advocates while amplifying the environmental impact of their purchase decision.",
                "sources": ["S2", "S4", "S9"],
                "difference": "Unlike conventional approaches that focus on the buyer's impact alone, this hypothesis leverages the social influence motivation of environmentally conscious buyers, creating a network effect that extends beyond traditional marketing reach."
            },
            {
                "hypothesis": "If we develop a 'BMW Forest' program where each vehicle purchased contributes to reforestation with real-time tracking via an exclusive app, then environmentally conscious luxury car buyers will experience ongoing positive reinforcement of their purchase decision",
                "rationale": "Research indicates that environmentally conscious consumers suffer from purchase regret without continued reinforcement of the positive impact of their choices. A real-time, personalized connection to environmental restoration addresses this need while creating an emotional bond with the brand.",
                "sources": ["S3", "S7"],
                "difference": "This approach moves beyond the one-time validation of an environmentally sound purchase to create an evolving relationship with the customer through continual positive reinforcement and tangible impact visualization."
            }
        ]
    }
    ```
    """

    hypotheses: List[Dict[str, Any]] = Field(
        ...,
        description="List of 5-10 innovative marketing hypotheses with supporting rationale, source references, and explanation of differences",
        min_items=3,
        max_items=10,
        examples=[[
            {
                "hypothesis": "If we create exclusive 'carbon offset credits' that BMW EV buyers can gift to others, then environmentally conscious luxury car buyers will become brand ambassadors who expand our reach beyond direct marketing",
                "rationale": "Research shows that environmentally conscious consumers value the ability to influence others' behavior. By enabling BMW EV buyers to gift tangible environmental benefits to friends and family, we turn customers into advocates.",
                "sources": ["S2", "S4", "S9"],
                "difference": "Unlike conventional approaches that focus on the buyer's impact alone, this hypothesis leverages the social influence motivation of environmentally conscious buyers."
            }
        ]]
    )
    
    @validator('hypotheses')
    def validate_source_references(cls, hypotheses):
        """Validate that each hypothesis has the required fields, proper format, and explains differences."""
        for i, hyp in enumerate(hypotheses):
            # Check for required fields
            if "hypothesis" not in hyp or not hyp["hypothesis"]:
                raise ValueError(f"Hypothesis {i+1} is missing required field: hypothesis")
                
            # Validate hypothesis format
            hypothesis_text = hyp.get("hypothesis", "")
            if not ("If we" in hypothesis_text and "then" in hypothesis_text):
                raise ValueError(f"Hypothesis {i+1} must follow the format: 'If we [action], then [target audience] will [desired outcome]'")
            
            # Check for rationale
            if "rationale" not in hyp or not hyp["rationale"]:
                raise ValueError(f"Hypothesis {i+1} is missing required field: rationale")
                
            # Check rationale length
            if len(hyp.get("rationale", "").split()) < 20:
                raise ValueError(f"Hypothesis {i+1} has insufficient rationale: provide at least 2-3 sentences")
                
            # Check for sources
            if "sources" not in hyp or not hyp["sources"]:
                raise ValueError(f"Hypothesis {i+1} is missing source references")
                
            if not isinstance(hyp["sources"], list):
                raise ValueError(f"Hypothesis {i+1} sources must be a list of source IDs")
                
            if len(hyp["sources"]) < 1:
                raise ValueError(f"Hypothesis {i+1} must cite at least one source")
                
            # Check for difference explanation
            if "difference" not in hyp or not hyp["difference"]:
                raise ValueError(f"Hypothesis {i+1} is missing required field: difference")
                
            # Check difference explanation length
            if len(hyp.get("difference", "").split()) < 15:
                raise ValueError(f"Hypothesis {i+1} has insufficient explanation of how it differs from conventional approaches")
                
        return hypotheses


@CrewBase
class HypothesisCrew:
    """
    Hypothesis Generation Crew.
    This crew researches and generates marketing hypotheses for a brand/product.

    The crew consists of:
    1. Research Agent - Conducts initial research using exa.ai
    2. Obvious Hypotheses Agent - Generates straightforward marketing hypotheses
    3. Innovative Hypotheses Agent - Generates out-of-the-box marketing hypotheses
    """

    # Paths to YAML configuration files
    agents_config_path = "config/agents.yaml"
    tasks_config_path = "config/tasks.yaml"

    def __init__(self):
        """
        Initialize the crew with any necessary configuration
        """
        super().__init__()

        # Initialize the LLM with proper error handling
        self._initialize_llm()

        # Initialize the exa.ai search tool
        self._initialize_exa_search_tool()

        # Load configurations
        self.agents_config = self._load_config(self.agents_config_path)
        self.tasks_config = self._load_config(self.tasks_config_path)

        logger.info(
            f"Loaded agent configs: {list(self.agents_config.keys()) if self.agents_config else 'None'}"
        )
        logger.info(
            f"Loaded task configs: {list(self.tasks_config.keys()) if self.tasks_config else 'None'}"
        )

    def _initialize_llm(self) -> None:
        """
        Initialize the language model with more comprehensive error handling
        and configurable model parameters.
        
        Raises:
            ValueError: If the API key is not set or LLM initialization fails
        """
        # Get API key from environment variable
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            error_msg = "OPENAI_API_KEY environment variable is not set"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Get model configuration from environment variables or use defaults
        model_name = os.environ.get("HYPOTHESIS_LLM_MODEL", "gpt-4o")
        temperature = float(os.environ.get("HYPOTHESIS_LLM_TEMPERATURE", "0.2"))
        
        try:
            logger.info(f"Initializing LLM with model: {model_name}, temperature: {temperature}")
            self.llm = ChatOpenAI(
                model=model_name,
                temperature=temperature,
                api_key=api_key,
            )
            logger.info("LLM initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize LLM: {e}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e

    def _initialize_exa_search_tool(self) -> None:
        """
        Initialize the Exa search tool with improved error handling
        
        Raises:
            ValueError: If the API key is not set or tool initialization fails
        """
        # Get API key from environment variable
        exa_api_key = os.environ.get("EXA_API_KEY")
        if not exa_api_key:
            error_msg = "EXA_API_KEY environment variable is not set"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Get optional configuration from environment variables
        timeout = float(os.environ.get("EXA_TIMEOUT", "15"))
        max_retries = int(os.environ.get("EXA_MAX_RETRIES", "2"))
        retry_delay = float(os.environ.get("EXA_RETRY_DELAY", "2"))
        
        try:
            logger.info(f"Initializing Exa search tool")
            self.exa_search_tool = ExaSearchTool(
                api_key=exa_api_key,
                timeout=timeout,
                max_retries=max_retries,
                retry_delay=retry_delay
            )
            logger.info("Exa search tool initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize Exa search tool: {e}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e

    @log_errors(logger=logger, error_msg="Error loading configuration", reraise=True)
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from a YAML file with improved error handling

        Args:
            config_path: Path to the YAML file

        Returns:
            dict: Configuration from the YAML file

        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            ValueError: If the configuration file is empty or invalid
        """
        # Get the absolute path to the config file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(current_dir, config_path)

        logger.info(f"Loading config from: {full_path}")

        if not os.path.exists(full_path):
            error_msg = f"Config file not found at {full_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            with open(full_path, "r") as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            error_msg = f"Error parsing YAML in {full_path}: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        if not config:
            error_msg = f"Empty or invalid configuration in {full_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.debug(f"Successfully loaded {len(config)} configuration entries from {config_path}")
        return config

    @agent
    @log_errors(
        logger=logger, error_msg="Error creating researcher agent", reraise=True
    )
    def researcher(self) -> Agent:
        """
        Create the researcher agent using configuration from the YAML file
        """
        # Get agent configuration from YAML
        if "researcher" not in self.agents_config:
            logger.error("Required 'researcher' configuration not found in agents.yaml")
            raise ValueError("Missing 'researcher' configuration in agents.yaml file")
            
        config = self.agents_config["researcher"]
        logger.debug(f"Creating researcher agent with config: {config}")
        
        return Agent(
            config=config, llm=self.llm, tools=[self.exa_search_tool], verbose=True
        )

    @agent
    @log_errors(
        logger=logger,
        error_msg="Error creating obvious hypotheses specialist agent",
        reraise=True,
    )
    def obvious_hypotheses_specialist(self) -> Agent:
        """
        Create the obvious hypotheses specialist agent using configuration from the YAML file
        """
        # Get agent configuration from YAML
        if "obvious_hypotheses_specialist" not in self.agents_config:
            logger.error("Required 'obvious_hypotheses_specialist' configuration not found in agents.yaml")
            raise ValueError("Missing 'obvious_hypotheses_specialist' configuration in agents.yaml file")
            
        config = self.agents_config["obvious_hypotheses_specialist"]
        logger.debug(f"Creating obvious_hypotheses_specialist agent with config: {config}")
        
        return Agent(
            config=config, llm=self.llm, tools=[self.exa_search_tool], verbose=True
        )

    @agent
    @log_errors(
        logger=logger,
        error_msg="Error creating innovative hypotheses specialist agent",
        reraise=True,
    )
    def innovative_hypotheses_specialist(self) -> Agent:
        """
        Create the innovative hypotheses specialist agent using configuration from the YAML file
        """
        # Get agent configuration from YAML
        if "innovative_hypotheses_specialist" not in self.agents_config:
            logger.error("Required 'innovative_hypotheses_specialist' configuration not found in agents.yaml")
            raise ValueError("Missing 'innovative_hypotheses_specialist' configuration in agents.yaml file")
            
        config = self.agents_config["innovative_hypotheses_specialist"]
        logger.debug(f"Creating innovative_hypotheses_specialist agent with config: {config}")
        
        return Agent(
            config=config, llm=self.llm, tools=[self.exa_search_tool], verbose=True
        )

    @task
    @log_errors(logger=logger, error_msg="Error creating research task", reraise=True)
    def research_task(self) -> Task:
        """
        Create the research task using configuration from the YAML file
        """
        # Get task configuration from YAML
        if "research" not in self.tasks_config:
            logger.error("Required 'research' configuration not found in tasks.yaml")
            raise ValueError("Missing 'research' configuration in tasks.yaml file")
            
        task_config = dict(self.tasks_config["research"])
        logger.info(f"Creating research_task with config: {task_config}")

        return Task(
            config=task_config,
            agent=self.researcher(),
            output_pydantic=ResearchOutput,
            max_retries=3,  # Allow up to 3 retries if validation fails
        )

    @task
    @log_errors(
        logger=logger,
        error_msg="Error creating generate obvious hypotheses task",
        reraise=True,
    )
    def generate_obvious_hypotheses_task(self) -> Task:
        """
        Create the task to generate obvious hypotheses using configuration from the YAML file
        """
        # Get task configuration from YAML
        if "generate_obvious_hypotheses" not in self.tasks_config:
            logger.error("Required 'generate_obvious_hypotheses' configuration not found in tasks.yaml")
            raise ValueError("Missing 'generate_obvious_hypotheses' configuration in tasks.yaml file")
            
        task_config = dict(self.tasks_config["generate_obvious_hypotheses"])
        logger.info(f"Creating generate_obvious_hypotheses_task with config: {task_config}")

        return Task(
            config=task_config,
            agent=self.obvious_hypotheses_specialist(),
            context=[self.research_task()],
            output_pydantic=ObviousHypothesesOutput,
            max_retries=3,  # Allow up to 3 retries if validation fails
        )

    @task
    @log_errors(
        logger=logger,
        error_msg="Error creating generate innovative hypotheses task",
        reraise=True,
    )
    def generate_innovative_hypotheses_task(self) -> Task:
        """
        Create the task to generate innovative hypotheses using configuration from the YAML file
        """
        # Get task configuration from YAML
        if "generate_innovative_hypotheses" not in self.tasks_config:
            logger.error("Required 'generate_innovative_hypotheses' configuration not found in tasks.yaml")
            raise ValueError("Missing 'generate_innovative_hypotheses' configuration in tasks.yaml file")
            
        task_config = dict(self.tasks_config["generate_innovative_hypotheses"])
        logger.info(f"Creating generate_innovative_hypotheses_task with config: {task_config}")

        return Task(
            config=task_config,
            agent=self.innovative_hypotheses_specialist(),
            context=[self.research_task(), self.generate_obvious_hypotheses_task()],
            output_pydantic=InnovativeHypothesesOutput,
            max_retries=3,  # Allow up to 3 retries if validation fails
        )

    @crew
    @log_errors(logger=logger, error_msg="Error creating crew", reraise=True)
    def crew(self) -> Crew:
        """
        Create and return the crew.
        This method is called by the flow to get the crew.

        Returns:
            Crew: A configured CrewAI crew for hypothesis generation
        """
        logger.info("Creating crew with agents and tasks")
        return Crew(
            agents=[
                self.researcher(),
                self.obvious_hypotheses_specialist(),
                self.innovative_hypotheses_specialist(),
            ],
            tasks=[
                self.research_task(),
                self.generate_obvious_hypotheses_task(),
                self.generate_innovative_hypotheses_task(),
            ],
            process=Process.sequential,
            verbose=True,
        )

    @before_kickoff
    def before_crew_kickoff(self, inputs: Optional[Dict[str, Any]] = None) -> None:
        """
        Hook that runs before the crew is kicked off.
        Used for logging and validating inputs.

        Args:
            inputs: The inputs passed to the crew
        """
        logger.info(f"Starting crew execution with inputs: {inputs}")
        if not inputs:
            logger.warning("No inputs provided to the crew")
        else:
            missing = []
            for field in ["brand", "product", "audience", "goal"]:
                if field not in inputs or not inputs[field]:
                    missing.append(field)
            if missing:
                logger.warning(f"Missing required inputs: {', '.join(missing)}")

    @after_kickoff
    def after_crew_kickoff(self, result: Any) -> None:
        """
        Hook that runs after the crew has completed.
        Used for logging results.

        Args:
            result: The result of the crew execution
        """
        logger.info("Crew execution completed")
        if hasattr(result, "tasks_output") and result.tasks_output:
            logger.info(f"Crew produced {len(result.tasks_output)} task outputs")
        else:
            logger.warning("Crew did not produce any task outputs")
