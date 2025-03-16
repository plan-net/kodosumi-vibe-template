"""
Processing utilities for the CrewAI flow.
These functions handle error handling and local processing fallbacks.
"""

import time
import random
from typing import Dict, Any, List, Optional, Callable

from workflows.crewai_flow.data import SAMPLE_DATASETS
from workflows.crewai_flow.formatters import format_output

def process_insights_locally(insights: List[str]) -> List[Dict[str, Any]]:
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
        # Generate a priority score
        priority = random.randint(1, 10)
        
        processed_results.append({
            "insight": insight,
            "priority": priority,
            "processed_by": f"Local-{i}"
        })
    
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
        
    Note:
        This function is designed to be called from a flow's error handler method.
        It centralizes error handling logic outside the main flow class.
    """
    # Create fallback response
    fallback_data = create_fallback_response(flow_state.dataset_name)
    
    # Update the flow state with fallback data
    flow_state.analysis_results = fallback_data["analysis_results"]
    flow_state.parallel_processing_results = fallback_data["parallel_processing_results"]
    flow_state.final_insights = fallback_data["final_insights"]
    
    # Format the output based on the requested format
    return format_output(flow_state.final_insights, output_format) 