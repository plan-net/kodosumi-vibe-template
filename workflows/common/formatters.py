"""
Formatting utilities for the CrewAI flow.
These functions handle the formatting of flow outputs in different formats.
"""

import time
import json
import inspect
from typing import Dict, Any, List, Optional, Type, Union, get_type_hints
from pydantic import BaseModel

def format_output(
    data: Union[BaseModel, Dict[str, Any]], 
    output_format: str = "markdown",
    template: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Format the output based on the requested format (markdown or JSON).
    
    Args:
        data: The data to format (Pydantic model or dictionary)
        output_format: The desired output format ("markdown" or "json")
        template: Optional template configuration for markdown formatting
        
    Returns:
        The formatted output in the requested format
    """
    # Convert Pydantic model to dict if needed
    if isinstance(data, BaseModel):
        data_dict = data.model_dump()
    else:
        data_dict = data
    
    if output_format.lower() == "json":
        # For JSON format, return the raw data structure
        return data_dict
    else:
        # For markdown format, convert the data to a formatted markdown string
        return format_as_markdown(data_dict, template)

def format_as_markdown(
    data: Dict[str, Any], 
    template: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format the data as a markdown string with improved source tracking.
    
    Args:
        data: The data to format
        template: Optional template configuration for customizing the markdown output
        
    Returns:
        A formatted markdown string
    """
    # Default template settings
    default_template = {
        "title": "Report",
        "timestamp_field": "timestamp",
        "timestamp_format": "%Y-%m-%d %H:%M:%S",
        "sections": [],  # List of section configurations
        "include_timestamp": True,
    }
    
    # Merge provided template with defaults
    template = {**default_template, **(template or {})}
    
    # Get title from template or data
    title = data.get("title", template["title"])
    
    # Start building markdown
    markdown = f"# {title}\n\n"
    
    # Standard sections to display first
    standard_fields = ["brand", "product", "audience", "goal", "research_summary"]
    
    # Process standard sections first
    for field in standard_fields:
        if field in data:
            # Convert snake_case to Title Case for section headers
            section_title = " ".join(word.capitalize() for word in field.split("_"))
            markdown += f"## {section_title}\n{data[field]}\n\n"
    
    # Create source lookup if available
    source_lookup = {}
    sources = data.get("sources", [])
    if sources:
        markdown += "## Sources\n"
        
        for i, source in enumerate(sources, 1):
            source_id = source.get("id", f"S{i}")
            source_lookup[source_id] = source
            
            title = source.get("title", "No title available")
            url = source.get("url", "#")
            summary = source.get("summary", "No summary available")
            
            markdown += f"{i}. **[{source_id}] {title}** - [Link]({url})\n"
            markdown += f"   *{summary}*\n\n"
    
    # Process hypotheses sections
    for hypothesis_type in ["obvious_hypotheses", "innovative_hypotheses"]:
        if hypothesis_type in data:
            # Title for the section
            section_title = " ".join(word.capitalize() for word in hypothesis_type.split("_"))
            markdown += f"## {section_title}\n"
            
            hypotheses = data[hypothesis_type]
            for i, hyp in enumerate(hypotheses, 1):
                hypothesis_text = hyp.get("hypothesis", "No hypothesis provided")
                markdown += f"{i}. **{hypothesis_text}**\n"
                
                # Add rationale
                if "rationale" in hyp:
                    markdown += f"   - *Rationale*: {hyp['rationale']}\n"
                
                # Add properly formatted source references
                if "sources" in hyp and hyp["sources"]:
                    source_refs = []
                    for src_id in hyp["sources"]:
                        if src_id in source_lookup:
                            source = source_lookup[src_id]
                            title = source.get("title", "Unknown source")
                            source_refs.append(f"[{src_id}] {title}")
                        else:
                            source_refs.append(f"[{src_id}]")
                    
                    markdown += f"   - *Sources*: {', '.join(source_refs)}\n"
                
                # Add difference explanation for innovative hypotheses
                if hypothesis_type == "innovative_hypotheses" and "difference" in hyp:
                    markdown += f"   - *Difference*: {hyp['difference']}\n"
                
                markdown += "\n"
    
    # Process any remaining non-standard fields
    for key, value in data.items():
        # Skip already processed fields and special fields
        if (key in standard_fields or 
            key in ["sources", "obvious_hypotheses", "innovative_hypotheses"] or
            key.startswith("_") or 
            key == template["timestamp_field"] or 
            key == "title"):
            continue
            
        # Convert snake_case to Title Case for section headers
        section_title = " ".join(word.capitalize() for word in key.split("_"))
        markdown += f"## {section_title}\n"
        
        if isinstance(value, list):
            # Format lists as numbered items
            for i, item in enumerate(value, 1):
                if isinstance(item, dict):
                    # For dictionaries in lists, use the first value as the main text
                    first_value = next(iter(item.values()), "")
                    markdown += f"{i}. **{first_value}**"
                    
                    # Add other key-value pairs in parentheses
                    other_items = [(k, v) for k, v in item.items() if v != first_value]
                    if other_items:
                        markdown += " ("
                        markdown += ", ".join(f"{k}: {v}" for k, v in other_items)
                        markdown += ")"
                    markdown += "\n"
                else:
                    markdown += f"{i}. {item}\n"
        elif isinstance(value, dict):
            # Format dictionaries as key-value pairs
            for k, v in value.items():
                markdown += f"**{k}**: {v}\n"
        else:
            # Simple value
            markdown += f"{value}\n"
            
        markdown += "\n"
    
    # Add timestamp footer if requested
    if template["include_timestamp"]:
        timestamp_field = template["timestamp_field"]
        timestamp = data.get(timestamp_field, time.strftime(template["timestamp_format"]))
        markdown += f"\n\n*Generated on {timestamp}*"
    
    return markdown

def format_dict_item(item: Dict[str, Any], item_format: Dict[str, Any]) -> str:
    """
    Format a dictionary item according to the specified format.
    
    Args:
        item: The dictionary item to format
        item_format: Format configuration for the item
        
    Returns:
        A formatted string representation of the item
    """
    # Default to using the first field as the main text
    main_field = item_format.get("main_field")
    if not main_field and item:
        main_field = next(iter(item.keys()))
    
    # Get the main text
    main_text = item.get(main_field, "")
    
    # Format the main text
    formatted = f"**{main_text}**"
    
    # Add additional fields if specified
    additional_fields = item_format.get("additional_fields", [])
    if additional_fields:
        additional = []
        for field in additional_fields:
            if field in item and field != main_field:
                additional.append(f"{field}: {item[field]}")
        
        if additional:
            formatted += f" ({', '.join(additional)})"
    
    return formatted

def pydantic_to_markdown_template(model_class: Type[BaseModel]) -> Dict[str, Any]:
    """
    Generate a markdown template based on a Pydantic model structure.
    
    Args:
        model_class: The Pydantic model class
        
    Returns:
        A template configuration for formatting instances of the model
    """
    template = {
        "title": model_class.__name__,
        "sections": []
    }
    
    # Get field information from the model
    fields = model_class.model_fields
    
    for field_name, field_info in fields.items():
        # Skip private fields
        if field_name.startswith("_"):
            continue
            
        # Get field type
        field_type = field_info.annotation
        
        # Determine format type based on field type
        format_type = "text"
        if "List" in str(field_type) or "list" in str(field_type):
            format_type = "list"
        elif "Dict" in str(field_type) or "dict" in str(field_type):
            format_type = "dict"
            
        # Create section config
        section = {
            "title": " ".join(word.capitalize() for word in field_name.split("_")),
            "field": field_name,
            "format": format_type
        }
        
        # Add item format for lists of dictionaries
        if format_type == "list":
            section["item_format"] = {
                "main_field": "",  # Will be determined at runtime
                "additional_fields": []  # Will be populated at runtime
            }
            
        template["sections"].append(section)
    
    return template

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