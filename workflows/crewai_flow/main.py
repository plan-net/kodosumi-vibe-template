#!/usr/bin/env python

"""
CrewAI Data Analysis Flow

This module defines a flow for data analysis using CrewAI and Ray.

Cursor Rules for AI Agents:
---------------------------
1. Output Format: This flow supports two output formats:
   - 'markdown': Human-readable format with headers and formatting (default)
   - 'json': Machine-readable format for agent-to-agent interactions
   
   When making API calls to this flow, AI agents should specify the 'output_format' 
   parameter as 'json' for easier parsing and processing of results.
   
   Example:
   ```python
   result = await kickoff({"dataset_name": "sales_data", "output_format": "json"})
   # Process the JSON result
   summary = result["summary"]
   insights = result["prioritized_insights"]
   ```

2. Dataset Selection: Valid dataset names are defined in the SAMPLE_DATASETS dictionary.
   Current options: 'sales_data', 'customer_feedback'

3. Error Handling: Invalid parameters will default to 'sales_data' for dataset_name
   and 'markdown' for output_format.
"""

import json
import os
import requests
import asyncio
import ray
import sys
import time
import random
from typing import List, Dict, Any

from dotenv import load_dotenv
from pydantic import BaseModel

from crewai.flow import Flow, listen, start

# Import your crew classes here
from workflows.crewai_flow.crews.first_crew.first_crew import FirstCrew, FirstCrewOutput

# Load environment variables from .env file
load_dotenv()

# Check if we're running in Kodosumi environment
# Kodosumi will handle Ray initialization for us
is_kodosumi = os.environ.get("KODOSUMI_ENVIRONMENT") == "true"

# Sample datasets for demonstration
SAMPLE_DATASETS = {
    "sales_data": {
        "name": "Quarterly Sales Data",
        "description": "Sales data for the last 4 quarters across different regions and product categories.",
        "sample": [
            {"quarter": "Q1", "region": "North", "category": "Electronics", "sales": 125000},
            {"quarter": "Q1", "region": "South", "category": "Electronics", "sales": 87000},
            {"quarter": "Q1", "region": "East", "category": "Furniture", "sales": 118000},
            {"quarter": "Q1", "region": "West", "category": "Clothing", "sales": 92000},
            {"quarter": "Q2", "region": "North", "category": "Electronics", "sales": 132000},
            {"quarter": "Q2", "region": "South", "category": "Furniture", "sales": 97000},
            {"quarter": "Q3", "region": "East", "category": "Clothing", "sales": 105000},
            {"quarter": "Q4", "region": "West", "category": "Electronics", "sales": 145000}
        ]
    },
    "customer_feedback": {
        "name": "Customer Feedback Survey",
        "description": "Results from a recent customer satisfaction survey with ratings and comments.",
        "sample": [
            {"customer_id": 1001, "rating": 4.5, "comment": "Great product, fast delivery!"},
            {"customer_id": 1002, "rating": 3.0, "comment": "Product was okay, but shipping took too long."},
            {"customer_id": 1003, "rating": 5.0, "comment": "Excellent customer service and quality."},
            {"customer_id": 1004, "rating": 2.5, "comment": "The product didn't meet my expectations."},
            {"customer_id": 1005, "rating": 4.0, "comment": "Good value for money, would recommend."}
        ]
    }
}

class CrewAIFlowState(BaseModel):
    """
    Define your flow state here.
    This will hold all the data that is passed between steps in the flow.
    """
    dataset_name: str = "sales_data"  # Default dataset
    output_format: str = "markdown"   # Default output format (markdown or json)
    analysis_results: Dict[str, Any] = None
    parallel_processing_results: List[Dict[str, Any]] = []
    final_insights: Dict[str, Any] = None

    @property
    def is_valid_output_format(self) -> bool:
        """Check if the output format is valid."""
        return self.output_format.lower() in ["markdown", "json"]

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
        print("Validating inputs...")
        
        # Check if the dataset exists
        if self.state.dataset_name not in SAMPLE_DATASETS:
            print(f"Dataset '{self.state.dataset_name}' not found. Using default dataset.")
            self.state.dataset_name = "sales_data"
        
        print(f"Using dataset: {self.state.dataset_name}")

    @listen(validate_inputs)
    def analyze_data(self):
        """
        First step in the flow.
        This step uses Ray to execute a CrewAI crew task remotely.
        """
        print("Analyzing data...")
        
        # Get the selected dataset
        dataset = SAMPLE_DATASETS[self.state.dataset_name]
        
        # Use Ray to execute the first crew task
        # This will run the crew kickoff on a Ray worker
        result_ref = ray.remote(FirstCrew().crew().kickoff).remote(
            inputs={
                "dataset_name": dataset["name"],
                "dataset_description": dataset["description"],
                "sample_data": json.dumps(dataset["sample"], indent=2)
            }
        )
        
        # Wait for the result
        result = ray.get(result_ref)
        
        # Parse the result
        if isinstance(result.raw, str):
            try:
                parsed_result = json.loads(result.raw)
            except json.JSONDecodeError:
                # If the result is not valid JSON, create a simple structure
                parsed_result = {
                    "summary": result.raw,
                    "insights": ["Could not parse insights"],
                    "recommendations": ["Could not parse recommendations"]
                }
        else:
            parsed_result = result.raw
            
        self.state.analysis_results = parsed_result
        print("Data analysis completed.")

    @listen(analyze_data)
    def process_insights_in_parallel(self):
        """
        Second step in the flow.
        This step demonstrates how to parallelize processing of multiple items using Ray.
        """
        print("Processing insights in parallel...")
        
        # Extract insights from the analysis results
        insights = self.state.analysis_results.get("insights", [])
        
        if not insights:
            print("No insights to process.")
            return
        
        # Define a remote function to process each insight
        @ray.remote
        def process_insight(insight, index):
            """Process a single insight using Ray."""
            # Simulate some processing time
            time.sleep(random.uniform(0.5, 2.0))
            
            # Generate a priority score based on the insight (just for demonstration)
            priority = random.randint(1, 10)
            
            return {
                "insight": insight,
                "priority": priority,
                "processed_by": f"Worker-{index}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        
        # Process all insights in parallel
        process_tasks = [process_insight.remote(insight, i) for i, insight in enumerate(insights)]
        processed_results = ray.get(process_tasks)
        
        # Sort results by priority (highest first)
        self.state.parallel_processing_results = sorted(
            processed_results, 
            key=lambda x: x["priority"], 
            reverse=True
        )
        
        print(f"Processed {len(processed_results)} insights in parallel.")

    @listen(process_insights_in_parallel)
    def finalize_results(self):
        """
        Final step in the flow.
        This step aggregates the results from previous steps.
        """
        print("Finalizing results...")
        
        # Combine the original analysis with the prioritized insights
        self.state.final_insights = {
            "summary": self.state.analysis_results.get("summary", "No summary available"),
            "prioritized_insights": self.state.parallel_processing_results,
            "recommendations": self.state.analysis_results.get("recommendations", []),
            "dataset_analyzed": self.state.dataset_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        print("Flow completed successfully!")
        
        # Print a summary of the results
        print("\n=== ANALYSIS RESULTS ===")
        print(f"Dataset: {SAMPLE_DATASETS[self.state.dataset_name]['name']}")
        print(f"Summary: {self.state.final_insights['summary'][:200]}...")
        print("\nTop 3 Prioritized Insights:")
        for i, insight in enumerate(self.state.final_insights['prioritized_insights'][:3], 1):
            print(f"{i}. {insight['insight']} (Priority: {insight['priority']})")
        print("\nRecommendations:")
        for i, rec in enumerate(self.state.final_insights['recommendations'][:3], 1):
            print(f"{i}. {rec}")
        print("========================\n")
        
        # Format the output based on the requested format
        if not self.state.is_valid_output_format:
            print(f"Invalid output format: {self.state.output_format}. Using default (markdown).")
            self.state.output_format = "markdown"
            
        if self.state.output_format.lower() == "json":
            # For JSON format, return the raw data structure
            return self.state.final_insights
        else:
            # For markdown format, convert the data to a formatted markdown string
            return self._format_as_markdown(self.state.final_insights)
    
    def _format_as_markdown(self, insights: Dict[str, Any]) -> str:
        """
        Format the insights as a markdown string.
        
        Args:
            insights: The insights to format
            
        Returns:
            A markdown formatted string
        """
        dataset_name = SAMPLE_DATASETS[insights["dataset_analyzed"]]["name"]
        
        # Build the markdown output
        md = [
            f"# Analysis Results for {dataset_name}",
            "",
            f"*Analysis completed at: {insights['timestamp']}*",
            "",
            "## Summary",
            "",
            insights["summary"],
            "",
            "## Key Insights (Prioritized)",
            ""
        ]
        
        # Add prioritized insights
        for i, insight in enumerate(insights["prioritized_insights"], 1):
            md.append(f"{i}. **{insight['insight']}** *(Priority: {insight['priority']})*")
        
        md.append("")
        md.append("## Recommendations")
        md.append("")
        
        # Add recommendations
        for i, rec in enumerate(insights["recommendations"], 1):
            md.append(f"{i}. {rec}")
        
        # Join all lines with newlines
        return "\n".join(md)

async def kickoff(inputs: dict):
    """
    Kickoff function for the flow.
    This is the entry point for the flow when called from Kodosumi.
    
    Args:
        inputs: A dictionary of inputs to the flow
            - dataset_name: The name of the dataset to analyze
            - output_format: The format of the output (markdown or json)
        
    Returns:
        The final state of the flow, formatted according to output_format
    """
    # Initialize Ray if not already initialized and not in Kodosumi environment
    if not ray.is_initialized() and not is_kodosumi:
        ray_address = os.environ.get("RAY_ADDRESS")
        if ray_address:
            print(f"Connecting to Ray cluster at {ray_address}")
            ray.init(address=ray_address)
        else:
            print("Initializing local Ray instance")
            ray.init()
        print(f"Ray initialized: {ray.cluster_resources()}")
    
    # Create the flow state with inputs
    state = CrewAIFlowState()
    
    # Update state with inputs
    if inputs and isinstance(inputs, dict):
        for key, value in inputs.items():
            if hasattr(state, key):
                setattr(state, key, value)
    
    # Validate output format
    if not state.is_valid_output_format:
        print(f"Invalid output format: {state.output_format}. Using default (markdown).")
        state.output_format = "markdown"
    
    # Create and run the flow
    flow = CrewAIFlow(state=state)
    result = await flow.start()
    
    # Return the result in the requested format
    if state.output_format.lower() == "json":
        return flow.state.dict()
    else:
        # For markdown, we return the formatted result from finalize_results
        return result


def plot():
    """
    Plot the flow graph.
    Useful for debugging and visualization.
    """
    flow = CrewAIFlow()
    flow.plot()


def init_ray():
    """
    Initialize Ray with appropriate configuration.
    This is used when running locally.
    """
    # Check if we should connect to an existing Ray cluster
    ray_address = os.environ.get("RAY_ADDRESS")
    
    if ray_address:
        # Connect to an existing Ray cluster
        print(f"Connecting to Ray cluster at {ray_address}")
        ray.init(address=ray_address)
    else:
        # Start a new local Ray instance
        print("Starting a new local Ray instance")
        ray.init()


if __name__ == "__main__":
    """
    Main entry point for the flow when run directly.
    """
    # Parse command line arguments
    args = {}
    for arg in sys.argv[1:]:
        if "=" in arg:
            key, value = arg.split("=", 1)
            args[key] = value
    
    # Run the flow
    result = asyncio.run(kickoff(args))
    
    # Print the result
    print("\nFlow execution completed.")
    
    # Shutdown Ray if we initialized it
    if ray.is_initialized() and not is_kodosumi:
        print("Shutting down Ray...")
        ray.shutdown()
        print("Ray shutdown complete.") 