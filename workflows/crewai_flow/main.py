#!/usr/bin/env python

import json
import os
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
        print("Validating inputs...")
        
        # Check if the dataset exists
        if self.state.dataset_name not in SAMPLE_DATASETS:
            print(f"Dataset '{self.state.dataset_name}' not found. Using default dataset.")
            self.state.dataset_name = "customer_feedback"
        
        print(f"Using dataset: {self.state.dataset_name}")

    @listen(validate_inputs)
    def analyze_data(self):
        """
        Analyze the selected dataset using CrewAI.
        This step creates a crew of AI agents to analyze the data.
        """
        dataset = SAMPLE_DATASETS[self.state.dataset_name]
        
        try:
            print(f"Using CrewAI to analyze {dataset['name']}...")
            
            # Create the crew (no output_format parameter needed)
            crew_instance = FirstCrew()
            crew = crew_instance.crew()
            
            # Prepare the task inputs
            task_inputs = {
                "dataset_name": dataset["name"],
                "dataset_description": dataset["description"],
                "sample_data": json.dumps(dataset["sample"], indent=2)
            }
            
            # Run the crew
            crew_result = crew.kickoff(inputs=task_inputs)
            
            # Use the structured output directly
            try:
                # The last task's output is the BusinessInsightsOutput
                if hasattr(crew_result, 'tasks_output') and len(crew_result.tasks_output) > 0:
                    # Get the output from the last task (insights task)
                    insights_output = crew_result.tasks_output[-1]
                    
                    # Store the structured output in the state
                    self.state.analysis_results = {
                        "summary": insights_output.summary,
                        "insights": insights_output.insights,
                        "recommendations": insights_output.recommendations
                    }
                else:
                    # Fallback if tasks_output is not available
                    raise ValueError("No structured output available from the crew")
                
                print("CrewAI analysis completed successfully.")
            except Exception as parsing_error:
                print(f"Error accessing crew output: {parsing_error}")
                raise
                
            return process_insights_in_parallel
        except Exception as e:
            print(f"Error during CrewAI analysis: {e}")
            return handle_error

    @listen(analyze_data)
    def process_insights_in_parallel(self):
        """
        Process the insights in parallel.
        This step prioritizes the insights based on their importance.
        """
        print("Processing insights in parallel...")
        
        # Extract insights from the analysis results
        insights = self.state.analysis_results.get("insights", [])
        
        if not insights:
            print("No insights to process.")
            return
        
        # Process insights using Ray
        try:
            # Define a remote function to process each insight
            @ray.remote
            def process_insight(insight, index):
                """Process a single insight using Ray."""
                # Simulate some processing time
                time.sleep(random.uniform(0.5, 1.0))
                
                # Generate a priority score based on the insight
                priority = random.randint(1, 10)
                
                return {
                    "insight": insight,
                    "priority": priority,
                    "processed_by": f"Worker-{index}"
                }
            
            # Process all insights in parallel
            print("Using Ray for parallel processing...")
            process_tasks = [process_insight.remote(insight, i) for i, insight in enumerate(insights)]
            processed_results = ray.get(process_tasks)
            
        except Exception as e:
            # Fallback to local processing if Ray fails
            print(f"Ray processing failed: {e}. Falling back to local processing...")
            processed_results = []
            for i, insight in enumerate(insights):
                # Simulate some processing time
                time.sleep(random.uniform(0.1, 0.3))
                
                # Generate a priority score
                priority = random.randint(1, 10)
                
                processed_results.append({
                    "insight": insight,
                    "priority": priority,
                    "processed_by": f"Local-{i}"
                })
        
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
        print(f"Summary: {self.state.final_insights['summary']}")
        print("\nTop 3 Prioritized Insights:")
        for i, insight in enumerate(self.state.final_insights['prioritized_insights'][:3], 1):
            print(f"{i}. {insight['insight']} (Priority: {insight['priority']})")
        print("\nRecommendations:")
        for i, rec in enumerate(self.state.final_insights['recommendations'][:3], 1):
            print(f"{i}. {rec}")
        print("========================\n")
        
        # Format the output based on the requested format
        return self._format_output(self.state.final_insights)
    
    def _format_output(self, insights: Dict[str, Any]) -> Any:
        """
        Format the output based on the requested format (markdown or JSON).
        This is the last step in the flow that ensures the output is in the desired format.
        
        Args:
            insights: The insights to format
            
        Returns:
            The formatted output (markdown string or JSON object)
        """
        if self.state.output_format.lower() == "json":
            # For JSON format, return the raw data structure
            return insights
        else:
            # For markdown format, convert the data to a formatted markdown string
            return self._format_as_markdown(insights)
    
    def _format_as_markdown(self, insights: Dict[str, Any]) -> str:
        """
        Format the insights as a markdown string.
        
        Args:
            insights: The insights to format
            
        Returns:
            A markdown formatted string
        """
        dataset_name = insights.get("dataset_analyzed", "Unknown dataset")
        timestamp = insights.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S"))
        summary = insights.get("summary", "No summary available")
        prioritized_insights = insights.get("prioritized_insights", [])
        recommendations = insights.get("recommendations", [])
        
        markdown = f"""# Data Analysis Report: {dataset_name}

## Summary
{summary}

## Key Insights
"""
        
        # Add prioritized insights
        for i, insight in enumerate(prioritized_insights, 1):
            priority = insight.get("priority", "Unknown")
            insight_text = insight.get("insight", "No insight available")
            markdown += f"{i}. **{insight_text}** (Priority: {priority})\n"
        
        # Add recommendations
        markdown += "\n## Recommendations\n"
        for i, recommendation in enumerate(recommendations, 1):
            markdown += f"{i}. {recommendation}\n"
        
        # Add footer
        markdown += f"\n\n*Generated on {timestamp}*"
        
        return markdown

    def handle_error(self):
        """
        Handle errors that occur during the flow execution.
        This method provides a graceful fallback when errors occur.
        """
        print("An error occurred during flow execution.")
        
        # Create a fallback response
        dataset_name = self.state.dataset_name
        dataset = SAMPLE_DATASETS.get(dataset_name, {"name": "Unknown dataset"})
        
        # Fallback analysis results
        self.state.analysis_results = {
            "summary": f"Unable to analyze {dataset['name']} due to an error.",
            "insights": ["Error occurred during analysis."],
            "recommendations": ["Please try again later."]
        }
        
        # Fallback prioritized insights
        self.state.parallel_processing_results = [
            {"insight": "Error occurred during analysis.", "priority": "High"}
        ]
        
        # Set final insights for output
        self.state.final_insights = {
            "summary": self.state.analysis_results["summary"],
            "prioritized_insights": self.state.parallel_processing_results,
            "recommendations": self.state.analysis_results["recommendations"],
            "dataset_analyzed": self.state.dataset_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        print("Using fallback response due to error.")
        
        # Format the output based on the requested format
        return self._format_output(self.state.final_insights)

async def kickoff(inputs: dict = None):
    """
    Kickoff function for the flow.
    This is the entry point for the flow when called from Kodosumi.
    """
    # Initialize Ray if not already initialized and not in Kodosumi environment
    if not ray.is_initialized() and not is_kodosumi:
        print("Initializing local Ray instance")
        ray.init()
    
    # Create the flow
    flow = CrewAIFlow()
    
    # Update state with inputs if provided
    if inputs and isinstance(inputs, dict):
        for key, value in inputs.items():
            if hasattr(flow.state, key):
                setattr(flow.state, key, value)
    
    # Run the flow
    result = await flow.kickoff_async()
    
    # Return the result
    return result

if __name__ == "__main__":
    """Main entry point for the flow when run directly."""
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