# Common Utilities Reference

## Overview

This reference guide documents the common utilities available in the `workflows/common` directory. These utilities provide shared functionality for formatting output, processing data, and managing resources across different workflows.

## Formatters (`formatters.py`)

### `format_output`

Formats workflow output in the requested format.

```python
from workflows.common.formatters import format_output

result = format_output(
    insights="Analysis results...",
    format="markdown"  # or "json"
)
```

**Parameters:**
- `insights` (str|dict): The insights to format
- `format` (str): Output format ("markdown" or "json")
- `title` (str, optional): Title for markdown output

**Returns:**
- Formatted string in markdown or JSON format

### `format_as_markdown`

Formats insights into a markdown string.

```python
from workflows.common.formatters import format_as_markdown

markdown = format_as_markdown(
    insights="Analysis results...",
    title="Analysis Report"
)
```

**Parameters:**
- `insights` (str|dict): Content to format
- `title` (str, optional): Report title

**Returns:**
- Markdown formatted string

### `extract_structured_data`

Extracts structured data from a CrewAI crew result.

```python
from workflows.common.formatters import extract_structured_data

data = extract_structured_data(crew_result)
```

**Parameters:**
- `crew_result` (str): Raw crew output

**Returns:**
- Dictionary of extracted data

## Processors (`processors.py`)

### `process_text_input`

Processes and validates text input.

```python
from workflows.common.processors import process_text_input

processed = process_text_input(
    text="Raw input...",
    max_length=1000
)
```

**Parameters:**
- `text` (str): Input text to process
- `max_length` (int, optional): Maximum allowed length
- `strip_html` (bool, optional): Remove HTML tags

**Returns:**
- Processed text string

### `validate_output_format`

Validates the requested output format.

```python
from workflows.common.processors import validate_output_format

is_valid = validate_output_format("markdown")
```

**Parameters:**
- `format` (str): Format to validate

**Returns:**
- bool: True if valid, False otherwise

### `clean_crew_output`

Cleans and standardizes crew output.

```python
from workflows.common.processors import clean_crew_output

cleaned = clean_crew_output(raw_output)
```

**Parameters:**
- `output` (str): Raw crew output

**Returns:**
- Cleaned output string

## Utils (`utils.py`)

### Ray Management

#### `initialize_ray`

Initializes or connects to a Ray cluster.

```python
from workflows.common.utils import initialize_ray

initialize_ray(
    address="auto",
    namespace="my_workflow"
)
```

**Parameters:**
- `address` (str, optional): Ray cluster address
- `namespace` (str, optional): Ray namespace
- `runtime_env` (dict, optional): Runtime environment

#### `shutdown_ray`

Safely shuts down Ray connection.

```python
from workflows.common.utils import shutdown_ray

shutdown_ray()
```

#### `test_ray_connectivity`

Tests connection to Ray cluster.

```python
from workflows.common.utils import test_ray_connectivity

is_connected = test_ray_connectivity()
```

**Returns:**
- bool: True if connected, False otherwise

### Error Handling

#### `handle_workflow_error`

Handles workflow execution errors.

```python
from workflows.common.utils import handle_workflow_error

try:
    # Workflow code
except Exception as e:
    error_response = handle_workflow_error(e)
```

**Parameters:**
- `error` (Exception): The caught exception
- `context` (dict, optional): Additional context

**Returns:**
- Dictionary with error details

### Configuration

#### `load_config`

Loads workflow configuration.

```python
from workflows.common.utils import load_config

config = load_config("my_workflow")
```

**Parameters:**
- `workflow_name` (str): Name of the workflow
- `config_path` (str, optional): Custom config path

**Returns:**
- Configuration dictionary

#### `validate_env`

Validates required environment variables.

```python
from workflows.common.utils import validate_env

validate_env([
    "OPENAI_API_KEY",
    "RAY_ADDRESS"
])
```

**Parameters:**
- `required_vars` (list): Required variable names

**Raises:**
- `EnvironmentError`: If variables are missing

## Usage Examples

### Complete Workflow Example

```python
from workflows.common import utils, formatters, processors

# Initialize resources
utils.validate_env(["OPENAI_API_KEY"])
utils.initialize_ray()

try:
    # Process input
    input_text = processors.process_text_input(
        raw_input,
        max_length=2000
    )
    
    # Run workflow
    result = my_workflow.run(input_text)
    
    # Format output
    output = formatters.format_output(
        result,
        format="markdown",
        title="Analysis Results"
    )
    
except Exception as e:
    error = utils.handle_workflow_error(e)
    raise
finally:
    utils.shutdown_ray()
```

### Error Handling Example

```python
from workflows.common.utils import handle_workflow_error
from workflows.common.processors import validate_output_format

try:
    if not validate_output_format(format):
        raise ValueError(f"Invalid format: {format}")
        
    # Workflow code...
    
except Exception as e:
    error_response = handle_workflow_error(
        e,
        context={"workflow": "analysis"}
    )
    return error_response
```

## Best Practices

1. **Resource Management**
   ```python
   try:
       utils.initialize_ray()
       # Workflow code
   finally:
       utils.shutdown_ray()
   ```

2. **Input Validation**
   ```python
   text = processors.process_text_input(
       input_text,
       max_length=1000,
       strip_html=True
   )
   ```

3. **Output Formatting**
   ```python
   if format == "markdown":
       return formatters.format_as_markdown(
           result,
           title="Report"
       )
   return formatters.format_output(
       result,
       format="json"
   )
   ```

## Common Issues

1. **Ray Connection Issues**
   ```python
   if not utils.test_ray_connectivity():
       utils.initialize_ray(address="auto")
   ```

2. **Environment Variables**
   ```python
   try:
       utils.validate_env(["OPENAI_API_KEY"])
   except EnvironmentError as e:
       print("Missing required environment variables")
       raise
   ```

3. **Output Format Validation**
   ```python
   if not processors.validate_output_format(format):
       raise ValueError(f"Unsupported format: {format}")
   ``` 