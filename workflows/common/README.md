# Common Utilities for CrewAI Workflows

This directory contains shared utilities and helper functions that can be used across different CrewAI workflows. These utilities provide standardized ways to handle common tasks such as formatting output, processing data in parallel, and managing Ray resources.

## Contents

### `formatters.py`

Utilities for formatting workflow outputs in different formats (markdown or JSON).

- **`format_output()`**: Converts data (Pydantic models or dictionaries) to either JSON or markdown format
- **`format_as_markdown()`**: Formats data as a markdown string with customizable templates
- **`pydantic_to_markdown_template()`**: Generates a markdown template based on a Pydantic model structure
- **`extract_structured_data()`**: Extracts structured data from CrewAI crew results

**Key Features:**
- Support for both Pydantic models and dictionaries as input
- Customizable markdown templates
- Auto-generation of markdown sections based on data structure
- Consistent timestamp formatting

### `processors.py`

Utilities for parallel processing, error handling, and fallbacks.

- **`process_with_ray_or_locally()`**: Processes items in parallel using Ray if available, or locally if not
- **`create_fallback_response()`**: Creates a fallback response when processing fails
- **`handle_flow_error()`**: Handles errors in the flow and returns appropriate responses

**Key Features:**
- Automatic fallback to local processing when Ray is unavailable
- Batch processing for better resource utilization
- Standardized error handling

### `utils.py`

Utility functions for Ray initialization, configuration, and management.

- **`initialize_ray()`**: Initializes or connects to a Ray cluster
- **`shutdown_ray()`**: Shuts down Ray when no longer needed
- **`test_ray_connectivity()`**: Tests connectivity to the Ray cluster

**Key Features:**
- Environment variable configuration for Ray settings
- Compatibility with Kodosumi deployment
- Patching for common Ray issues

### `data.py`

Common data structures and sample datasets for testing and demonstration.

- **`SAMPLE_DATASETS`**: Dictionary of sample datasets for testing workflows

## Usage

Import these utilities in your workflow files:

```python
from workflows.common.formatters import format_output
from workflows.common.processors import process_with_ray_or_locally
from workflows.common.utils import initialize_ray, shutdown_ray
```

## Best Practices

1. **Formatting Output**: Always use `format_output()` to format your workflow's final output, supporting both markdown and JSON formats.

2. **Parallel Processing**: Use `process_with_ray_or_locally()` for parallel processing tasks to automatically handle Ray availability.

3. **Ray Management**: Initialize Ray at the beginning of your workflow and shut it down at the end using the provided utilities.

4. **Error Handling**: Implement proper error handling using the provided utilities to ensure graceful degradation.

5. **Templates**: For complex markdown output, create custom templates to control the formatting.

## Example

```python
from workflows.common.formatters import format_output
from workflows.common.utils import initialize_ray, shutdown_ray

# Initialize Ray
initialize_ray()

# Process data and generate results
results = {
    "title": "Analysis Results",
    "summary": "Summary of the analysis",
    "insights": [
        {"insight": "First insight", "priority": 9},
        {"insight": "Second insight", "priority": 7}
    ],
    "recommendations": [
        "First recommendation",
        "Second recommendation"
    ],
    "timestamp": "2023-01-01 12:00:00"
}

# Format the output based on the requested format
formatted_output = format_output(results, "markdown")

# Shut down Ray
shutdown_ray()
``` 