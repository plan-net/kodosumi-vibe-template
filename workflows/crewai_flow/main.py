#!/usr/bin/env python
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
# from crewai_flow.crews.first_crew.first_crew import FirstCrew, FirstCrewOutput
# from crewai_flow.crews.second_crew.second_crew import SecondCrew
# from crewai_flow.crews.third_crew.third_crew import ThirdCrew

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
    input_param1: str = "default_value"
    input_param2: str = "default_value"
    step1_output: dict = None
    step2_output: list = []
    step3_output: dict = None
    parallel_processing_results: List[Dict[str, Any]] = []


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
        print("Validating your inputs ...")
        # Add your validation logic here

    @listen(validate_inputs)
    def step1(self):
        """
        First step in the flow.
        This step is executed after validate_inputs.
        
        This demonstrates how to use Ray to execute a CrewAI crew task remotely.
        """
        print("Executing step 1 ...")
        
        # Use Ray to execute the first crew task
        # Uncomment and modify this code when you have your crew ready
        """
        # This will run the crew kickoff on a Ray worker
        result_ref = ray.remote(FirstCrew().crew().kickoff).remote(
            inputs={"param1": self.state.input_param1, "param2": self.state.input_param2}
        )
        result = ray.get(result_ref)
        
        # Parse the result
        if isinstance(result.raw, str):
            parsed_result = json.loads(result.raw)
        else:
            parsed_result = result.raw
            
        self.state.step1_output = parsed_result
        """
        
        # For template purposes, just set a dummy output
        self.state.step1_output = {"status": "completed", "data": "step1 output"}
        print("Step 1 completed.")

    @listen(step1)
    def step2(self):
        """
        Second step in the flow.
        This step is executed after step1.
        
        This demonstrates how to parallelize processing of multiple items using Ray.
        """
        print("Executing step 2 ...")
        
        # Example of a function that could be parallelized with Ray
        @ray.remote
        def process_item(item):
            """
            This function will be executed on a Ray worker.
            
            In a real-world scenario, this could be a computationally intensive task like:
            - Processing a large document
            - Running a machine learning model
            - Performing a complex calculation
            - Making an API call
            """
            # Simulate some processing time
            time.sleep(random.uniform(0.5, 2.0))
            
            # Process the item
            return {
                "processed_item": item,
                "status": "processed",
                "timestamp": time.time(),
                "worker_id": ray.get_runtime_context().get_node_id()
            }
        
        # Example of parallel processing with Ray
        items = ["item1", "item2", "item3", "item4", "item5"]
        
        # Create a list of remote tasks
        # Each task will be scheduled on an available Ray worker
        process_tasks = [process_item.remote(item) for item in items]
        
        # Wait for all tasks to complete and get the results
        # This is non-blocking - we can do other work while these tasks run
        processed_results = ray.get(process_tasks)
        
        self.state.step2_output = processed_results
        print(f"Step 2 completed with {len(processed_results)} processed items.")

    @listen(step2)
    def step3_parallel_processing(self):
        """
        Third step in the flow.
        This step demonstrates more advanced parallel processing patterns with Ray.
        """
        print("Executing step 3 (advanced parallel processing) ...")
        
        # Define a more complex task that might require significant resources
        @ray.remote(num_cpus=1)  # Request specific resources
        def complex_processing_task(data, config):
            """
            A more complex processing task that might require specific resources.
            
            Args:
                data: The data to process
                config: Configuration parameters for the processing
            
            Returns:
                The processed result
            """
            # Simulate complex processing
            time.sleep(random.uniform(1.0, 3.0))
            
            # In a real scenario, this could be:
            # - Training a machine learning model
            # - Processing a large dataset
            # - Running a complex simulation
            
            return {
                "input_data": data,
                "config": config,
                "result": f"Processed {data} with {config}",
                "worker_info": {
                    "node_id": ray.get_runtime_context().get_node_id(),
                    "job_id": ray.get_runtime_context().get_job_id()
                }
            }
        
        # Define a task that depends on the results of other tasks
        @ray.remote
        def aggregation_task(results):
            """
            A task that aggregates results from other tasks.
            
            Args:
                results: A list of results from other tasks
                
            Returns:
                The aggregated result
            """
            # Simulate aggregation processing
            time.sleep(1.0)
            
            # In a real scenario, this could:
            # - Combine results from multiple models
            # - Perform statistical analysis on multiple outputs
            # - Generate a summary report
            
            return {
                "num_results": len(results),
                "aggregated_data": [r["result"] for r in results],
                "timestamp": time.time()
            }
        
        # Create a set of data items to process
        data_items = [f"data_{i}" for i in range(10)]
        configs = [{"param": f"value_{i}"} for i in range(10)]
        
        # Launch the processing tasks
        processing_refs = [
            complex_processing_task.remote(data, config)
            for data, config in zip(data_items, configs)
        ]
        
        # Wait for all processing tasks to complete
        # This demonstrates how to handle dependencies between tasks
        processing_results = ray.get(processing_refs)
        
        # Launch the aggregation task with the results from the processing tasks
        aggregation_ref = aggregation_task.remote(processing_results)
        
        # Wait for the aggregation task to complete
        aggregation_result = ray.get(aggregation_ref)
        
        # Store the results
        self.state.parallel_processing_results = {
            "processing_results": processing_results,
            "aggregation_result": aggregation_result
        }
        
        print(f"Step 3 completed with {len(processing_results)} processed items and aggregation.")
        
    @listen(step3_parallel_processing)
    def step4_final(self):
        """
        Final step in the flow.
        This step is executed after step3_parallel_processing.
        
        This demonstrates how to use Ray to execute a final CrewAI crew task remotely.
        """
        print("Executing final step ...")
        
        # Use Ray to execute the third crew task
        # Uncomment and modify this code when you have your crew ready
        """
        result_ref = ray.remote(ThirdCrew().crew().kickoff).remote(
            inputs={
                "step1_output": self.state.step1_output,
                "step2_output": self.state.step2_output,
                "parallel_processing_results": self.state.parallel_processing_results
            }
        )
        result = ray.get(result_ref)
        self.state.step3_output = result.raw
        """
        
        # For template purposes, just set a dummy output
        self.state.step3_output = {
            "status": "completed", 
            "summary": "All steps completed successfully",
            "data": {
                "step1": self.state.step1_output,
                "step2": self.state.step2_output,
                "parallel_processing": self.state.parallel_processing_results
            }
        }
        
        print("Final step completed.")
        return self.state.step3_output

async def kickoff(inputs: dict):
    """
    Kickoff the flow with the given inputs.
    This function is called by the serve.py file.
    """
    flow = CrewAIFlow()
    
    # Set the inputs from the request
    if inputs:
        for key, value in inputs.items():
            if hasattr(flow.state, key):
                setattr(flow.state, key, value)
    
    # Kickoff the flow
    await flow.kickoff_async()


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
    try:
        # Only initialize Ray if we're not running in Kodosumi
        if not is_kodosumi:
            init_ray()
            
        # For local testing
        if len(sys.argv) > 1:
            # Parse command line arguments
            inputs = {}
            for arg in sys.argv[1:]:
                if '=' in arg:
                    key, value = arg.split('=', 1)
                    inputs[key] = value
            
            # Run the flow with the provided inputs
            asyncio.run(kickoff(inputs))
        else:
            # Run with default inputs
            asyncio.run(kickoff({}))
            
    finally:
        # Only shut down Ray if we're not running in Kodosumi and Ray is initialized
        if not is_kodosumi and ray.is_initialized():
            print("Shutting down Ray")
            ray.shutdown() 