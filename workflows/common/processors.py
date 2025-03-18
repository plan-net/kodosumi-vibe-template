"""
Processing utilities for CrewAI workflows.
These functions handle parallel processing, error handling, and fallbacks.
"""

import time
import random
import ray
from typing import Dict, Any, List, TypeVar, Callable, Optional

from workflows.common.formatters import format_output
from workflows.common.utils import (
    RAY_TASK_NUM_CPUS, RAY_TASK_MAX_RETRIES, RAY_TASK_TIMEOUT, RAY_BATCH_SIZE,
    test_ray_connectivity
)
from workflows.common.logging_utils import get_logger, log_errors, format_error_response

# Set up logger
logger = get_logger(__name__)

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
        logger.warning("No items to process.")
        return []
    
    # Test if Ray is working
    ray_working, _ = test_ray_connectivity()
    
    if ray_working:
        try:
            return _process_with_ray(items, process_func, batch_size)
        except Exception as e:
            logger.error(f"Error in Ray processing, falling back to local: {e}")
            return _process_locally(items, process_func)
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
    logger.info(f"Processing {len(items)} items with Ray in batches of {batch_size}...")
    
    # Define a remote function to process each item
    @ray.remote(num_cpus=RAY_TASK_NUM_CPUS, max_retries=RAY_TASK_MAX_RETRIES)
    def ray_process(item, index):
        return process_func(item, index)
    
    # Process items in batches
    processed_results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        batch_log_prefix = f"Batch {i//batch_size + 1}/{(len(items) + batch_size - 1)//batch_size}"
        logger.debug(f"{batch_log_prefix}: Processing {len(batch)} items")
        
        process_tasks = [ray_process.remote(item, i+j) for j, item in enumerate(batch)]
        
        try:
            batch_results = ray.get(process_tasks, timeout=RAY_TASK_TIMEOUT)
            processed_results.extend(batch_results)
            logger.debug(f"{batch_log_prefix}: Completed successfully")
        except (ray.exceptions.GetTimeoutError, TimeoutError) as e:
            logger.warning(f"{batch_log_prefix}: Timed out ({e}). Processing locally.")
            # Process this batch locally if timeout occurs
            for j, item in enumerate(batch):
                try:
                    result = process_func(item, i+j)
                    processed_results.append(result)
                except Exception as item_error:
                    logger.error(f"Error processing item {i+j}: {item_error}")
                    # Add a placeholder result to maintain order
                    processed_results.append(None)
    
    # Filter out None values (failed items)
    valid_results = [r for r in processed_results if r is not None]
    
    if len(valid_results) < len(items):
        logger.warning(f"Only {len(valid_results)}/{len(items)} items were processed successfully")
    
    return valid_results

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
    logger.info(f"Processing {len(items)} items locally...")
    
    processed_results = []
    
    for i, item in enumerate(items):
        try:
            result = process_func(item, i)
            processed_results.append(result)
            logger.debug(f"Processed item {i+1}/{len(items)}")
        except Exception as e:
            logger.error(f"Error processing item {i}: {e}")
    
    return processed_results

def create_fallback_response(dataset_name: str, error: Optional[Exception] = None) -> Dict[str, Any]:
    """
    Create a fallback response when an error occurs during flow execution.
    
    Args:
        dataset_name: The name of the dataset being analyzed
        error: Optional exception that occurred
        
    Returns:
        A dictionary containing fallback data
    """
    error_message = f"Unable to analyze {dataset_name}"
    if error:
        error_message += f": {str(error)}"
    
    logger.error(error_message)
    
    # Set fallback data
    analysis_results = {
        "summary": error_message,
        "insights": ["Error occurred during analysis."],
        "recommendations": ["Please try again later."]
    }
    
    parallel_processing_results = [
        {"insight": "Error occurred during analysis.", "priority": 10, "error_details": str(error) if error else "Unknown error"}
    ]
    
    final_insights = {
        "summary": analysis_results["summary"],
        "prioritized_insights": parallel_processing_results,
        "recommendations": analysis_results["recommendations"],
        "dataset_analyzed": dataset_name,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "error": True
    }
    
    return {
        "analysis_results": analysis_results,
        "parallel_processing_results": parallel_processing_results,
        "final_insights": final_insights
    }

@log_errors(logger=logger, error_msg="Error handling flow error")
def handle_flow_error(flow_state: Any, output_format: str = "markdown", error: Optional[Exception] = None) -> Any:
    """
    Handle errors that occur during flow execution.
    
    This function creates a fallback response when an error occurs during flow execution
    and updates the flow state with the fallback data.
    
    Args:
        flow_state: The flow state object to update
        output_format: The desired output format ("markdown" or "json")
        error: Optional exception that occurred
        
    Returns:
        The formatted fallback response
    """
    # Create fallback response
    fallback_data = create_fallback_response(flow_state.dataset_name, error)
    
    # Update the flow state with fallback data
    flow_state.analysis_results = fallback_data["analysis_results"]
    flow_state.parallel_processing_results = fallback_data["parallel_processing_results"]
    flow_state.final_insights = fallback_data["final_insights"]
    
    # Format the output based on the requested format
    return format_output(flow_state.final_insights, output_format)