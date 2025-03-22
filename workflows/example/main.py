#!/usr/bin/env python

import json
import os
import ray
import sys
import time
import random
import uuid
import re
import asyncio
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from pydantic import BaseModel
from kodosumi.dtypes import Markdown
from kodosumi.tracer import markdown

from crewai.flow import Flow, listen, start

# Import your crew classes here
from workflows.example.crews.first_crew.first_crew import FirstCrew
from workflows.common.data import SAMPLE_DATASETS
from workflows.common.utils import (
    initialize_ray, shutdown_ray
)
from workflows.common.formatters import format_output
from workflows.common.logging_utils import get_logger

# Set up logger
logger = get_logger(__name__)

# Load environment variables from .env file
load_dotenv()

# Check if we're running in Kodosumi environment
# Kodosumi will handle Ray initialization for us
is_kodosumi = os.environ.get("KODOSUMI_ENVIRONMENT") == "true"

# Define the Ray remote function
@ray.remote
def process_insight(insight):
    """
    Ray remote function to process a single insight.
    Args:
        insight: The insight text to process
    Returns:
        A dictionary with the processed insight data
    """
    # Generate a priority score based on the insight content
    # In a real application, this could use NLP or other techniques
    # to determine the importance of the insight
    priority = random.randint(1, 10)
    
    result = {
        "insight": insight,
        "priority": priority,
        "processed_by": f"Ray-Worker-{uuid.uuid4().hex[:8]}",
        "processing_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return result

class CrewAIFlowState(BaseModel):
    """
    Define your flow state here.
    This will hold all the data that is passed between steps in the flow.
    """
    dataset_name: str = "customer_feedback"  # Default dataset
    output_format: str = "markdown"   # Default output format (markdown or json)
    analysis_results: Dict[str, Any] = {}
    analysis_error: Optional[str] = None
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
        markdown("**Validating inputs...**")
        logger.info("Validating inputs...")
        
        # Check if the dataset exists
        if self.state.dataset_name not in SAMPLE_DATASETS:
            logger.warning(f"Dataset '{self.state.dataset_name}' not found. Using default dataset.")
            self.state.dataset_name = "customer_feedback"
        
        logger.info(f"Using dataset: {self.state.dataset_name}")
        markdown(f"**Using dataset: {self.state.dataset_name}**")

    @listen(validate_inputs)
    def analyze_data(self):
        """
        Analyze the input data using CrewAI.
        """
        markdown(f"**Analyzing {self.state.dataset_name} dataset using CrewAI...**")
        logger.info(f"Using CrewAI to analyze {self.state.dataset_name}...")
        
        try:
            # Get dataset from SAMPLE_DATASETS
            dataset = SAMPLE_DATASETS.get(self.state.dataset_name)
            if not dataset:
                raise ValueError(f"Dataset {self.state.dataset_name} not found in SAMPLE_DATASETS")
            
            # Prepare inputs for the crew
            task_inputs = {
                "dataset_name": dataset["name"],
                "dataset_description": dataset["description"],
                "sample_data": json.dumps(dataset["sample"], indent=2)
            }
            
            # Create and run the crew
            markdown(f"**Initializing agents for {self.state.dataset_name} analysis...**")
            crew_instance = FirstCrew()
            crew = crew_instance.crew()
            markdown("**Executing crew tasks to analyze the data...**")
            crew.kickoff(inputs=task_inputs)
            
            # Extract insights from the last task output
            if crew.tasks and len(crew.tasks) > 0:
                last_task = crew.tasks[-1]
                if last_task.output:
                    # Try to extract insights using the most reliable methods
                    insights_dict = self._extract_insights_from_task_output(last_task.output)
                    if insights_dict:
                        # Get some statistics about the insights for better reporting
                        insight_count = len(insights_dict.get("insights", []))
                        rec_count = len(insights_dict.get("recommendations", []))
                        
                        markdown(f"**Analysis complete. Found {insight_count} insights and {rec_count} recommendations.**")
                        self.state.analysis_results = insights_dict
                        return self.process_insights_in_parallel
            
            # If we reach here, create fallback results
            markdown("**Unable to extract structured insights from crew output. Creating fallback results.**")
            self.state.analysis_error = f"Unable to extract insights for {self.state.dataset_name} dataset."
            self.state.analysis_results = {
                "summary": f"Analysis of {self.state.dataset_name} was completed, but insights extraction failed.",
                "insights": [f"No insights could be properly extracted for {self.state.dataset_name}."],
                "recommendations": ["Try with a different dataset or check the task output format."]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing data: {str(e)}")
            markdown(f"**Error during analysis: {str(e)}**")
            self.state.analysis_error = str(e)
            self.state.analysis_results = {
                "summary": f"Analysis of {self.state.dataset_name} failed due to an error.",
                "insights": [f"Error: {str(e)}"],
                "recommendations": ["Try again later."]
            }
        
        return self.process_insights_in_parallel

    def _extract_insights_from_task_output(self, task_output):
        """
        Helper method to extract insights from task output using various methods.
        Returns a dictionary with the insights or None if extraction fails.
        """
        # Method 1: Extract from raw output (most reliable)
        if hasattr(task_output, 'raw'):
            try:
                match = re.search(r'\{[\s\S]*\}', task_output.raw)
                if match:
                    insights_dict = json.loads(match.group(0))
                    if isinstance(insights_dict, dict) and 'insights' in insights_dict:
                        return insights_dict
            except Exception:
                pass
        
        # Method 2: Try direct attribute access
        if hasattr(task_output, 'summary') and hasattr(task_output, 'insights'):
            return {
                "summary": task_output.summary,
                "insights": task_output.insights,
                "recommendations": getattr(task_output, 'recommendations', [])
            }
        
        # Method 3: Try using __dict__
        if hasattr(task_output, '__dict__'):
            insights_dict = task_output.__dict__
            if isinstance(insights_dict, dict) and 'insights' in insights_dict:
                return insights_dict
        
        return None

    @listen(analyze_data)
    async def process_insights_in_parallel(self):
        """Process insights in parallel."""
        markdown("**Processing insights in parallel...**")
        logger.info("Processing insights in parallel...")

        try:
            if not hasattr(self.state, 'analysis_results') or not self.state.analysis_results:
                logger.warning("No analysis results found in state")
                markdown("**Warning: No analysis results found to process.**")
                self.state.parallel_processing_results = []
                return self.finalize_results

            # Extract insights from the analysis results
            logger.info(f"Analysis results type: {type(self.state.analysis_results)}")
            
            if isinstance(self.state.analysis_results, dict) and 'insights' in self.state.analysis_results:
                logger.info(f"Analysis results keys: {self.state.analysis_results.keys()}")
                insights = self.state.analysis_results.get('insights', [])
                
                if insights:
                    count = len(insights)
                    logger.info(f"Processing {count} insights")
                    markdown(f"**Processing {count} insights from {self.state.dataset_name} dataset...**")
                    
                    # Process insights asynchronously
                    start_time = time.time()
                    
                    # Create remote tasks
                    refs = [process_insight.remote(insight) for insight in insights]
                    
                    # Process with asyncio as suggested by Ray's warning
                    coroutines = [asyncio.to_thread(ray.get, ref) for ref in refs]
                    insights_results = await asyncio.gather(*coroutines)
                    
                    processing_time = time.time() - start_time
                    self.state.parallel_processing_results = insights_results
                    
                    # Group insights by priority for better presentation
                    high_priority = [i for i in insights_results if i.get('priority', 0) >= 8]
                    medium_priority = [i for i in insights_results if 4 <= i.get('priority', 0) < 8]
                    low_priority = [i for i in insights_results if i.get('priority', 0) < 4]
                    
                    logger.info(f"Processed {len(insights_results)} insights")
                    markdown(f"**Completed processing {len(insights_results)} insights in {processing_time:.2f} seconds.**")
                    return self.finalize_results
                else:
                    logger.warning("Insights list is empty")
                    markdown("**Warning: Insights list is empty.**")
            else:
                logger.warning(f"Analysis results does not contain 'insights' key")
                markdown("**Warning: Analysis results does not contain 'insights' key.**")
            
            logger.warning("No insights to process. Using empty result set.")
            self.state.parallel_processing_results = []
            return self.finalize_results
        except Exception as e:
            logger.error(f"Error processing insights: {str(e)}")
            markdown(f"**Error during processing: {str(e)}**")
            self.state.parallel_processing_results = [{"error": f"Error processing insights: {str(e)}"}]
            return self.finalize_results

    @listen(process_insights_in_parallel)
    async def finalize_results(self):
        """
        Final step in the flow.
        This step aggregates the results from previous steps.
        """
        markdown("**Finalizing results and generating report...**")
        logger.info("Finalizing results...")
        
        # Get counts for better reporting
        insight_count = len(self.state.parallel_processing_results)
        rec_count = len(self.state.analysis_results.get("recommendations", []))
        
        # Combine the original analysis with the prioritized insights
        self.state.final_insights = {
            "summary": self.state.analysis_results.get("summary", "No summary available"),
            "prioritized_insights": self.state.parallel_processing_results,
            "recommendations": self.state.analysis_results.get("recommendations", []),
            "dataset_analyzed": self.state.dataset_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        logger.info("Flow completed successfully!")
        markdown(f"**Workflow complete! Analyzed {self.state.dataset_name} dataset with {len(self.state.parallel_processing_results)} insights.**")
        
        # Format the output based on the requested format
        return format_output(self.state.final_insights, self.state.output_format)

def kickoff(inputs: dict = None):
    """
    Kickoff function for the flow.
    This is the entry point for the flow when called from Kodosumi.
    """
    # Initialize Ray if needed
    initialize_ray(is_kodosumi)
    
    try:
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
        
        # Run the flow
        logger.info("Starting flow execution...")
        markdown(f"**Starting CrewAI Insights Generator for {flow.state.dataset_name} dataset in {flow.state.output_format} format.**")
        result = flow.kickoff()
        logger.info("Flow execution completed successfully")
        
        return Markdown(body=result)
    except Exception as e:
        logger.error(f"Error during flow execution: {e}", exc_info=True)
        # Return a fallback response in case of error
        error_message = format_output({
            "error": str(e), 
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "workflow": "CrewAI Insights Generator",
            "status": "Failed"
        }, "markdown")
        return Markdown(body=error_message)
    finally:
        # Shutdown Ray if needed
        shutdown_ray(is_kodosumi)

# Add metadata to the kickoff function
kickoff.__brief__ = {
    "summary": "Customer Insights Generator",
    "description": "Analyzes customer feedback data using CrewAI and generates prioritized insights with recommendations.",
    "author": "Kodosumi AI Team",
    "organization": "Kodosumi"
}

def plot():
    """Generate and display a flow diagram for the CrewAI Flow."""
    flow = CrewAIFlow()
    flow.plot()

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
        result = kickoff(args)
        
        # Print the result (extract body from Markdown object if needed)
        logger.info("Flow execution completed.")
        if hasattr(result, 'body'):
            print("\n" + result.body)
        else:
            print("\n" + str(result))
    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True)
        print(f"\nError: {e}")
        sys.exit(1)