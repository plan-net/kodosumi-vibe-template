"""
Processing utilities for the CrewAI flow.
These functions handle parallel processing, error handling, and fallbacks.
"""

import time
import random
import ray
from typing import Dict, Any, List, TypeVar, Callable

from workflows.crewai_flow.data import SAMPLE_DATASETS
from workflows.crewai_flow.formatters import format_output
from workflows.crewai_flow.utils import (
    RAY_TASK_NUM_CPUS, RAY_TASK_MAX_RETRIES, RAY_TASK_TIMEOUT, RAY_BATCH_SIZE,
    test_ray_connectivity
)

# Type variables for generic functions
T = TypeVar('T')  # Input type
R = TypeVar('R')  # Result type

def process_with_ray_or_locally(
    items: List[T],
    process_func: Callable[[T, int], R],
    batch_size: int = RAY_BATCH_SIZE
) -> List[R]:
    """
    Process a list of items either with Ray (if available) or locally.
    
    This function attempts to process items in parallel using Ray.
    If Ray is not available or fails, it falls back to local processing.
    
    Args:
        items: List of items to process
        process_func: Function to process each item, taking (item, index) as arguments
        batch_size: Number of items to process in each batch
        
    Returns:
        List of processed results
    """
    if not items:
        print("No items to process.")
        return []
    
    # Test if Ray is working
    ray_working, _ = test_ray_connectivity()
    
    if ray_working:
        return _process_with_ray(items, process_func, batch_size)
    else:
        return _process_locally(items, process_func)

def _process_with_ray(
    items: List[T],
    process_func: Callable[[T, int], R],
    batch_size: int = RAY_BATCH_SIZE
) -> List[R]:
    """
    Process items in parallel using Ray.
    
    Args:
        items: List of items to process
        process_func: Function to process each item, taking (item, index) as arguments
        batch_size: Number of items to process in each batch
        
    Returns:
        List of processed results
    """
    print("Processing items with Ray...")
    
    # Define a remote function to process each item
    @ray.remote(num_cpus=RAY_TASK_NUM_CPUS, max_retries=RAY_TASK_MAX_RETRIES)
    def ray_process(item, index):
        return process_func(item, index)
    
    # Process items in batches
    processed_results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        process_tasks = [ray_process.remote(item, i+j) for j, item in enumerate(batch)]
        
        try:
            batch_results = ray.get(process_tasks, timeout=RAY_TASK_TIMEOUT)
            processed_results.extend(batch_results)
        except (ray.exceptions.GetTimeoutError, TimeoutError) as e:
            print(f"Ray batch processing timed out: {e}. Processing this batch locally.")
            # Process this batch locally if timeout occurs
            for j, item in enumerate(batch):
                processed_results.append(process_func(item, i+j))
    
    return processed_results

def _process_locally(
    items: List[T],
    process_func: Callable[[T, int], R]
) -> List[R]:
    """
    Process items locally (without Ray).
    
    Args:
        items: List of items to process
        process_func: Function to process each item, taking (item, index) as arguments
        
    Returns:
        List of processed results
    """
    print("Processing items locally...")
    
    processed_results = []
    
    for i, item in enumerate(items):
        processed_results.append(process_func(item, i))
    
    return processed_results 

def create_fallback_response(dataset_name: str) -> Dict[str, Any]:
    """
    Create a fallback response when an error occurs during flow execution.
    
    Args:
        dataset_name: The name of the dataset being analyzed
        
    Returns:
        A dictionary containing fallback data
    """
    print("An error occurred during flow execution.")
    
    # Get dataset information
    dataset = SAMPLE_DATASETS.get(dataset_name, {"name": "Unknown dataset"})
    
    # Set fallback data
    analysis_results = {
        "summary": f"Unable to analyze {dataset['name']} due to an error.",
        "insights": ["Error occurred during analysis."],
        "recommendations": ["Please try again later."]
    }
    
    parallel_processing_results = [
        {"insight": "Error occurred during analysis.", "priority": 10}
    ]
    
    final_insights = {
        "summary": analysis_results["summary"],
        "prioritized_insights": parallel_processing_results,
        "recommendations": analysis_results["recommendations"],
        "dataset_analyzed": dataset_name,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return {
        "analysis_results": analysis_results,
        "parallel_processing_results": parallel_processing_results,
        "final_insights": final_insights
    }

def handle_flow_error(flow_state: Any, output_format: str = "markdown") -> Any:
    """
    Handle errors that occur during flow execution.
    
    This function creates a fallback response when an error occurs during flow execution
    and updates the flow state with the fallback data.
    
    Args:
        flow_state: The flow state object to update
        output_format: The desired output format ("markdown" or "json")
        
    Returns:
        The formatted fallback response
    """
    # Create fallback response
    fallback_data = create_fallback_response(flow_state.dataset_name)
    
    # Update the flow state with fallback data
    flow_state.analysis_results = fallback_data["analysis_results"]
    flow_state.parallel_processing_results = fallback_data["parallel_processing_results"]
    flow_state.final_insights = fallback_data["final_insights"]
    
    # Format the output based on the requested format
    return format_output(flow_state.final_insights, output_format)

