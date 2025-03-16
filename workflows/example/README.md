# CrewAI Flow Template

This template provides a structured approach to building CrewAI flows with parallel processing capabilities.

## Code Organization

The codebase is organized into the following components:

### Main Flow (`main.py`)

The main flow class that orchestrates the entire process:
- `CrewAIFlowState`: Holds the state of the flow
- `CrewAIFlow`: Defines the flow steps and logic
  - `validate_inputs`: Validates input parameters
  - `analyze_data`: Uses CrewAI to analyze data
  - `process_insights_in_parallel`: Processes insights using Ray or locally
  - `process_insight`: Processes a single insight (kept in main.py for visibility)
  - `finalize_results`: Aggregates results and formats output

### Data Management (`data.py`)

Contains sample datasets and data structures:
- `SAMPLE_DATASETS`: Dictionary of sample datasets for testing

### Utility Functions (`utils.py`)

Ray-related utility functions:
- Environment variable configurations
- `apply_ray_patch`: Fixes Ray's FilteredStream isatty error
- `initialize_ray`: Handles Ray initialization with fallbacks
- `shutdown_ray`: Safely shuts down Ray
- `test_ray_connectivity`: Tests if Ray is working properly

### Processing Utilities (`processors.py`)

Functions for parallel processing and error handling:
- `create_fallback_response`: Creates a response when errors occur
- `handle_flow_error`: Centralizes error handling logic
- `process_with_ray_or_locally`: Generic function for parallel processing that automatically falls back to local processing when Ray is unavailable

### Output Formatting (`formatters.py`)

Functions for formatting and extracting data:
- `format_output`: Formats output in markdown or JSON
- `extract_structured_data`: Extracts structured data from crew results

### Crew Definitions (`crews/`)

Contains crew definitions used in the flow:
- `first_crew/`: Example crew with agents and tasks

## Design Decisions

1. **Process Insight Function**: Kept in `main.py` for better visibility and tracking, as it's a core part of the flow logic.

2. **Ray Utilities**: Moved to a separate file to keep the main flow clean and focused on business logic.

3. **Generic Processing**: Implemented a generic `process_with_ray_or_locally` function that can be used with any processing function and automatically falls back to local processing when Ray is unavailable.

4. **Error Handling**: Centralized error handling in utility functions to reduce code duplication.

5. **Simplified Fallback Mechanism**: Removed specialized fallback functions in favor of the generic processing function that handles both Ray and local processing.

## Usage

To run the flow:

```bash
python -m workflows.crewai_flow.main
```

## Customization

To customize the flow:

1. Modify the `CrewAIFlowState` class to include your own state variables
2. Add or modify flow steps in the `CrewAIFlow` class
3. Create your own crew definitions in the `crews/` directory
4. Update the `process_insight` function to implement your own logic 