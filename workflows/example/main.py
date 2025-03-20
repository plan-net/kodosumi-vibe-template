#!/usr/bin/env python

import json
import os
import asyncio
import ray
import sys
import time
import random
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from pydantic import BaseModel

from crewai.flow import Flow, listen, start

# Import your crew classes here
from workflows.example.crews.first_crew.first_crew import FirstCrew
from workflows.common.data import SAMPLE_DATASETS
from workflows.common.utils import (
    RAY_TASK_NUM_CPUS, RAY_TASK_MAX_RETRIES, RAY_TASK_TIMEOUT, 
    RAY_BATCH_SIZE, initialize_ray, shutdown_ray, test_ray_connectivity
)
from workflows.common.formatters import format_output, extract_structured_data
from workflows.common.processors import (
    create_fallback_response, handle_flow_error,
    process_with_ray_or_locally
)
from workflows.common.logging_utils import get_logger, log_errors

# Set up logger
logger = get_logger(__name__)

# Load environment variables from .env file
load_dotenv()

# Check if we're running in Kodosumi environment
# Kodosumi will handle Ray initialization for us
is_kodosumi = os.environ.get("KODOSUMI_ENVIRONMENT") == "true"

class CrewAIFlowState(BaseModel):
    """
    Define your flow state here.
    This will hold all the data that is passed between steps in the flow.
    """
    dataset_name: str = "customer_feedback"  # Default dataset
    output_format: str = "markdown"   # Default output format (markdown or json)
    analysis_results: Dict[str, Any] = {}
    parallel_processing_results: List[Dict[str, Any]] = []
    final_insights: Dict[str, Any] = {}

class CrewAIFlow(Flow[CrewAIFlowState]):
    """
    Define your flow steps here.
    Each step is a method decorated with @listen that takes the output of a previous step.
    """

    @start()
    def validate_inputs(self):
        """
        Validate the inputs to the flow.
        This is the first step in the flow.
        """
        logger.info("Validating inputs...")
        
        # Check if the dataset exists
        if self.state.dataset_name not in SAMPLE_DATASETS:
            logger.warning(f"Dataset '{self.state.dataset_name}' not found. Using default dataset.")
            self.state.dataset_name = "customer_feedback"
        
        logger.info(f"Using dataset: {self.state.dataset_name}")

    @listen(validate_inputs)
    def analyze_data(self):
        """
        Analyze the selected dataset using CrewAI.
        
        This step creates a crew of AI agents to analyze the data and extract insights.
        The crew is defined in the FirstCrew class and is responsible for:
        1. Analyzing the dataset to identify patterns and trends
        2. Generating business insights and recommendations
        
        The structured output from the crew is stored in the flow state for further processing.
        """
        dataset = SAMPLE_DATASETS[self.state.dataset_name]
        
        try:
            logger.info(f"Using CrewAI to analyze {dataset['name']}...")
            
            # Create and run the crew
            crew_instance = FirstCrew()
            crew = crew_instance.crew()
            
            # Prepare the task inputs with dataset information
            task_inputs = {
                "dataset_name": dataset["name"],
                "dataset_description": dataset["description"],
                "sample_data": json.dumps(dataset["sample"], indent=2)
            }
            
            # Run the crew and get the result
            crew_result = crew.kickoff(inputs=task_inputs)
            
            # Extract structured data from the crew result
            json_data = extract_structured_data(crew_result)
            
            if json_data:
                # Store the structured output in the state
                self.state.analysis_results = {
                    "summary": json_data.get("summary", "No summary available"),
                    "insights": json_data.get("insights", []),
                    "recommendations": json_data.get("recommendations", [])
                }
                logger.info("CrewAI analysis completed successfully.")
                return self.process_insights_in_parallel
            else:
                logger.error("No structured output available from the crew.")
                # Call the utility function directly instead of using a wrapper method
                return handle_flow_error(self.state, self.state.output_format)
        except Exception as e:
            logger.error(f"Error during CrewAI analysis: {e}", exc_info=True)
            # Call the utility function directly instead of using a wrapper method
            return handle_flow_error(self.state, self.state.output_format, error=e)

    @listen(analyze_data)
    def process_insights_in_parallel(self):
        """
        Process insights in parallel using Ray.
        This step takes the insights from the analysis and processes them in parallel.
        """
        logger.info("Processing insights in parallel...")
        
        # Extract insights from the analysis results
        insights = self.state.analysis_results.get("insights", [])
        
        if not insights:
            logger.warning("No insights to process. Using empty result set.")
            self.state.parallel_processing_results = []
            return
        
        try:
            # Process insights using the generalized function
            # This will automatically use Ray if available, or fall back to local processing
            self.state.parallel_processing_results = process_with_ray_or_locally(
                items=insights,
                process_func=self.process_insight,
                batch_size=RAY_BATCH_SIZE
            )
        except Exception as e:
            # If the generic processing function fails completely, create a minimal result
            logger.error(f"Processing failed completely: {e}. Creating minimal results.", exc_info=True)
            self.state.parallel_processing_results = [
                {
                    "insight": "Error processing insights.",
                    "priority": 10,
                    "processed_by": "Error-Handler",
                    "error": str(e)
                }
            ]
        
        # Sort results by priority (highest first)
        self.state.parallel_processing_results = sorted(
            self.state.parallel_processing_results, 
            key=lambda x: x["priority"], 
            reverse=True
        )
        
        logger.info(f"Processed {len(self.state.parallel_processing_results)} insights.")

    @log_errors(logger=logger, error_msg="Error processing individual insight")
    def process_insight(self, insight: str, index: int) -> Dict[str, Any]:
        """
        Process a single insight, generating a priority score.
        
        This function is used with process_with_ray_or_locally to process
        insights either locally or with Ray, depending on availability.
        
        Args:
            insight: The insight text to process
            index: The index of the insight in the original list
            
        Returns:
            A dictionary with the processed insight data
        """
        logger.debug(f"Processing insight {index}: {insight[:50]}...")
        
        # Generate a priority score based on the insight content
        # In a real application, this could use NLP or other techniques
        # to determine the importance of the insight
        priority = random.randint(1, 10)
        
        result = {
            "insight": insight,
            "priority": priority,
            "processed_by": f"Worker-{index}",
            "processing_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        logger.debug(f"Insight {index} assigned priority {priority}")
        return result

    @listen(process_insights_in_parallel)
    def finalize_results(self):
        """
        Final step in the flow.
        This step aggregates the results from previous steps.
        """
        logger.info("Finalizing results...")
        
        # Combine the original analysis with the prioritized insights
        self.state.final_insights = {
            "summary": self.state.analysis_results.get("summary", "No summary available"),
            "prioritized_insights": self.state.parallel_processing_results,
            "recommendations": self.state.analysis_results.get("recommendations", []),
            "dataset_analyzed": self.state.dataset_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        logger.info("Flow completed successfully!")
        
        # Format the output based on the requested format
        return format_output(self.state.final_insights, self.state.output_format)

async def kickoff(inputs: dict = None):
    """
    Kickoff function for the flow.
    This is the entry point for the flow when called from Kodosumi.
    """
    # Initialize Ray if needed
    initialize_ray(is_kodosumi)
    
    # Create the flow
    flow = CrewAIFlow()
    
    # Update state with inputs if provided
    if inputs and isinstance(inputs, dict):
        logger.info(f"Initializing flow with inputs: {inputs}")
        for key, value in inputs.items():
            if hasattr(flow.state, key):
                setattr(flow.state, key, value)
            else:
                logger.warning(f"Ignoring unknown input parameter: {key}")
    
    try:
        # Run the flow
        logger.info("Starting flow execution...")
        result = await flow.kickoff_async()
        logger.info("Flow execution completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error during flow execution: {e}", exc_info=True)
        # Return a fallback response in case of error
        return format_output({"error": str(e), "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}, "markdown")
    finally:
        # Shutdown Ray if needed
        shutdown_ray(is_kodosumi)

if __name__ == "__main__":
    """Main entry point for the flow when run directly."""
    try:
        # Parse command line arguments
        args = {}
        for arg in sys.argv[1:]:
            if "=" in arg:
                key, value = arg.split("=", 1)
                args[key] = value
        
        logger.info(f"Starting flow with command line arguments: {args}")
        
        # Run the flow
        result = asyncio.run(kickoff(args))
        
        # Print the result
        logger.info("Flow execution completed.")
        print("\n" + result)
    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True)
        print(f"\nError: {e}")
        sys.exit(1)