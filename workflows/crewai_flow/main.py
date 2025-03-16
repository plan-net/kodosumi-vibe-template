#!/usr/bin/env python

import json
import os
import asyncio
import ray
import sys
import time
import random
import traceback
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from pydantic import BaseModel

from crewai.flow import Flow, listen, start

# Import your crew classes here
from workflows.crewai_flow.crews.first_crew.first_crew import FirstCrew

# Load environment variables from .env file
load_dotenv()

# Check if we're running in Kodosumi environment
# Kodosumi will handle Ray initialization for us
is_kodosumi = os.environ.get("KODOSUMI_ENVIRONMENT") == "true"

# Ray configuration from environment variables with defaults
RAY_TASK_NUM_CPUS = float(os.environ.get("RAY_TASK_NUM_CPUS", "0.1"))
RAY_TASK_MAX_RETRIES = int(os.environ.get("RAY_TASK_MAX_RETRIES", "3"))
RAY_TASK_TIMEOUT = float(os.environ.get("RAY_TASK_TIMEOUT", "10.0"))
RAY_BATCH_SIZE = int(os.environ.get("RAY_BATCH_SIZE", "1"))
RAY_INIT_NUM_CPUS = int(os.environ.get("RAY_INIT_NUM_CPUS", "2"))
RAY_DASHBOARD_PORT = os.environ.get("RAY_DASHBOARD_PORT", "None")  # Use "None" for no dashboard

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
                    
                    print(f"Received output type: {type(insights_output).__name__}")
                    
                    # Try different methods to access the data
                    if hasattr(insights_output, 'dict'):
                        # Pydantic model
                        output_dict = insights_output.dict()
                        print("Using Pydantic model dict() method")
                    elif hasattr(insights_output, '__dict__'):
                        # Object with __dict__
                        output_dict = insights_output.__dict__
                        print("Using __dict__ attribute")
                    elif hasattr(insights_output, 'model_dump'):
                        # Newer Pydantic v2 models
                        output_dict = insights_output.model_dump()
                        print("Using model_dump() method")
                    else:
                        # Treat as dictionary directly
                        output_dict = insights_output
                        print("Treating output as dictionary directly")
                    
                    # Print available keys for debugging
                    print(f"Available keys in output: {list(output_dict.keys()) if isinstance(output_dict, dict) else 'Not a dictionary'}")
                    
                    # Check if we have a json_dict field that contains the actual structured data
                    if hasattr(insights_output, 'json_dict') and insights_output.json_dict:
                        print("Found json_dict field, using it for structured data")
                        json_data = insights_output.json_dict
                        
                        # Store the structured output in the state
                        self.state.analysis_results = {
                            "summary": json_data.get("summary", "No summary available"),
                            "insights": json_data.get("insights", []),
                            "recommendations": json_data.get("recommendations", [])
                        }
                    elif hasattr(insights_output, 'raw') and insights_output.raw:
                        print("Found raw field, attempting to parse JSON from it")
                        try:
                            # Try to parse JSON from the raw output
                            raw_text = insights_output.raw
                            # Extract JSON part if it's embedded in markdown or other text
                            if '{' in raw_text and '}' in raw_text:
                                json_start = raw_text.find('{')
                                json_end = raw_text.rfind('}') + 1
                                json_str = raw_text[json_start:json_end]
                                json_data = json.loads(json_str)
                                
                                # Store the structured output in the state
                                self.state.analysis_results = {
                                    "summary": json_data.get("summary", "No summary available"),
                                    "insights": json_data.get("insights", []),
                                    "recommendations": json_data.get("recommendations", [])
                                }
                            else:
                                raise ValueError("No JSON found in raw output")
                        except Exception as json_error:
                            print(f"Error parsing JSON from raw output: {json_error}")
                            # Use the summary directly from output_dict if available
                            self.state.analysis_results = {
                                "summary": output_dict.get("summary", "No summary available"),
                                "insights": [],
                                "recommendations": []
                            }
                    else:
                        # Try to extract data directly from the output
                        try:
                            # Try to access the output directly as a string and parse it
                            output_str = str(insights_output)
                            if '{' in output_str and '}' in output_str:
                                json_start = output_str.find('{')
                                json_end = output_str.rfind('}') + 1
                                json_str = output_str[json_start:json_end]
                                json_data = json.loads(json_str)
                                
                                # Store the structured output in the state
                                self.state.analysis_results = {
                                    "summary": json_data.get("summary", "No summary available"),
                                    "insights": json_data.get("insights", []),
                                    "recommendations": json_data.get("recommendations", [])
                                }
                                print("Successfully parsed JSON from output string")
                            else:
                                # Use the output_dict directly
                                self.state.analysis_results = {
                                    "summary": output_dict.get("summary", "No summary available"),
                                    "insights": output_dict.get("insights", []),
                                    "recommendations": output_dict.get("recommendations", [])
                                }
                        except Exception as e:
                            print(f"Error extracting data from output: {e}")
                            raise ValueError("No structured output available from the crew")
                
                print("CrewAI analysis completed successfully.")
            except Exception as parsing_error:
                print(f"Error accessing crew output: {parsing_error}")
                print(f"Error type: {type(parsing_error).__name__}")
                print(f"Traceback: {traceback.format_exc()}")
                return self.handle_error()
                
            return self.process_insights_in_parallel
        except Exception as e:
            print(f"Error during CrewAI analysis: {e}")
            print(f"Error type: {type(e).__name__}")
            print(f"Traceback: {traceback.format_exc()}")
            return self.handle_error()

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
        
        # Check if Ray is initialized
        if not ray.is_initialized():
            print("Ray is not initialized. Processing insights locally...")
            self.state.parallel_processing_results = self._process_insights_locally(insights)
            return
        
        # Process insights using Ray with improved error handling
        try:
            # Define a remote function to process each insight
            @ray.remote(num_cpus=RAY_TASK_NUM_CPUS, max_retries=RAY_TASK_MAX_RETRIES)  # Use configured resources and retries
            def process_insight(insight, index):
                """Process a single insight using Ray."""
                # Minimal processing time to reduce chance of timeouts
                time.sleep(0.05)
                
                # Generate a priority score based on the insight
                priority = random.randint(1, 10)
                
                return {
                    "insight": insight,
                    "priority": priority,
                    "processed_by": f"Worker-{index}"
                }
            
            # First try to process a single insight to test Ray functionality
            print("Testing Ray with a single insight...")
            try:
                test_result = ray.get(process_insight.remote(insights[0], 0), timeout=RAY_TASK_TIMEOUT)
                print(f"Ray test successful: {test_result}")
                use_ray = True
            except (ray.exceptions.GetTimeoutError, TimeoutError) as timeout_err:
                print(f"Ray test failed with timeout: {timeout_err}. Falling back to local processing for all insights.")
                use_ray = False
                self.state.parallel_processing_results = self._process_insights_locally(insights)
                return
            
            if use_ray:
                # Process insights in small batches with increased timeout
                print("Using Ray for parallel processing...")
                processed_results = []
                
                # Process in batches based on configuration
                batch_size = RAY_BATCH_SIZE
                for i in range(0, len(insights), batch_size):
                    batch = insights[i:i+batch_size]
                    process_tasks = [process_insight.remote(insight, i+j) for j, insight in enumerate(batch)]
                    
                    try:
                        # Use configured timeout for each batch
                        print(f"Processing batch {i//batch_size + 1} with {len(batch)} insights (timeout: {RAY_TASK_TIMEOUT}s)...")
                        batch_results = ray.get(process_tasks, timeout=RAY_TASK_TIMEOUT)
                        processed_results.extend(batch_results)
                        print(f"Successfully processed batch {i//batch_size + 1}")
                    except (ray.exceptions.GetTimeoutError, TimeoutError) as timeout_err:
                        print(f"Batch {i//batch_size + 1} timed out: {timeout_err}. Processing this batch locally...")
                        # Process the remaining insights locally
                        for j, insight in enumerate(batch):
                            processed_results.append({
                                "insight": insight,
                                "priority": random.randint(1, 10),
                                "processed_by": f"Local-{i+j}"
                            })
                
                print(f"Successfully processed {len(processed_results)} insights in total")
                self.state.parallel_processing_results = processed_results
        except Exception as e:
            # Fallback to local processing if Ray fails
            print(f"Ray processing failed with error: {e}")
            print(f"Error type: {type(e).__name__}")
            print(f"Traceback: {traceback.format_exc()}")
            print("Falling back to local processing...")
            self.state.parallel_processing_results = self._process_insights_locally(insights)
        
        # Sort results by priority (highest first)
        self.state.parallel_processing_results = sorted(
            self.state.parallel_processing_results, 
            key=lambda x: x["priority"], 
            reverse=True
        )
        
        print(f"Processed {len(self.state.parallel_processing_results)} insights in parallel.")

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

    def _process_insights_locally(self, insights):
        """
        Process insights locally without using Ray.
        
        Args:
            insights: List of insights to process
            
        Returns:
            List of processed insights with priority scores
        """
        print("Processing insights locally...")
        processed_results = []
        for i, insight in enumerate(insights):
            # Minimal processing time
            time.sleep(0.05)
            
            # Generate a priority score
            priority = random.randint(1, 10)
            
            processed_results.append({
                "insight": insight,
                "priority": priority,
                "processed_by": f"Local-{i}"
            })
        
        print(f"Completed local processing for {len(processed_results)} insights.")
        return processed_results

async def kickoff(inputs: dict = None):
    """
    Kickoff function for the flow.
    This is the entry point for the flow when called from Kodosumi.
    """
    # Initialize Ray if not already initialized and not in Kodosumi environment
    if not ray.is_initialized() and not is_kodosumi:
        # Apply patch for Ray's FilteredStream isatty error
        try:
            import sys
            class PatchedStream:
                def __init__(self, stream):
                    self.stream = stream
                
                def __getattr__(self, attr):
                    if attr == 'isatty':
                        return lambda: False
                    return getattr(self.stream, attr)
                
                def write(self, *args, **kwargs):
                    return self.stream.write(*args, **kwargs)
                
                def flush(self):
                    return self.stream.flush()
            
            # Apply the patch to stdout and stderr
            sys.stdout = PatchedStream(sys.stdout)
            sys.stderr = PatchedStream(sys.stderr)
            print("Applied patch for Ray's FilteredStream isatty error")
        except Exception as e:
            print(f"Failed to apply Ray patch: {e}")
        
        print("Initializing local Ray instance")
        try:
            # Try to connect to an existing Ray cluster first
            try:
                ray.init(address="auto", ignore_reinit_error=True)
                print("Connected to existing Ray cluster")
            except (ConnectionError, ValueError):
                # If connecting fails, start a new Ray instance with configured resources
                dashboard_port = None if RAY_DASHBOARD_PORT == "None" else int(RAY_DASHBOARD_PORT)
                ray.init(num_cpus=RAY_INIT_NUM_CPUS, dashboard_port=dashboard_port, ignore_reinit_error=True)
                print(f"Started new Ray instance with {RAY_INIT_NUM_CPUS} CPUs")
        except Exception as ray_init_error:
            print(f"Error initializing Ray: {ray_init_error}")
            print("Continuing without Ray parallelization")
    
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