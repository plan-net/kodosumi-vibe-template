"""
Formatting utilities for the CrewAI flow.
These functions handle the formatting of flow outputs in different formats.
"""

import time
import json
from typing import Dict, Any, List, Optional

def format_output(insights: Dict[str, Any], output_format: str = "markdown") -> Any:
    """
    Format the output based on the requested format (markdown or JSON).
    
    Args:
        insights: The insights data to format
        output_format: The desired output format ("markdown" or "json")
        
    Returns:
        The formatted output in the requested format
    """
    if output_format.lower() == "json":
        # For JSON format, return the raw data structure
        return insights
    else:
        # For markdown format, convert the data to a formatted markdown string
        return format_as_markdown(insights)

def format_as_markdown(insights: Dict[str, Any]) -> str:
    """
    Format the insights as a markdown string.
    
    Args:
        insights: The insights data to format
        
    Returns:
        A formatted markdown string
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

def extract_structured_data(crew_result: Any) -> Optional[Dict[str, Any]]:
    """
    Extract structured data from a CrewAI crew result.
    
    CrewAI agents often return structured data in JSON format, but the exact
    location and format can vary. This function attempts to extract that data
    using common patterns.
    
    Args:
        crew_result: The result from a CrewAI crew execution
        
    Returns:
        A dictionary containing the structured data, or None if extraction fails
        
    Note:
        This is a utility function that handles the complexity of extracting
        structured data from CrewAI outputs. In your own implementation, you may
        need to adjust this based on your specific crew's output format.
    """
    try:
        # Check if we have task outputs
        if not hasattr(crew_result, 'tasks_output') or not crew_result.tasks_output:
            return None
        
        # Get the last task output (typically contains the final result)
        last_task = crew_result.tasks_output[-1]
        
        # Method 1: Direct JSON dictionary access (most common)
        if hasattr(last_task, 'json_dict') and last_task.json_dict:
            return last_task.json_dict
        
        # Method 2: Parse from raw output
        if hasattr(last_task, 'raw') and last_task.raw:
            try:
                return json.loads(last_task.raw)
            except json.JSONDecodeError:
                # If direct parsing fails, try to extract JSON from text
                raw_text = last_task.raw
                if '{' in raw_text and '}' in raw_text:
                    json_start = raw_text.find('{')
                    json_end = raw_text.rfind('}') + 1
                    json_str = raw_text[json_start:json_end]
                    return json.loads(json_str)
        
        # Method 3: Last resort - try to parse the string representation
        output_str = str(last_task)
        if '{' in output_str and '}' in output_str:
            json_start = output_str.find('{')
            json_end = output_str.rfind('}') + 1
            json_str = output_str[json_start:json_end]
            return json.loads(json_str)
        
        return None
    except Exception:
        # Silently fail and return None if any error occurs
        return None 