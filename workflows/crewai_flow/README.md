# CrewAI Data Analysis Flow

This workflow demonstrates how to use CrewAI with Ray for distributed data analysis. It showcases a complete flow that analyzes data, processes insights in parallel, and returns formatted results.

## Features

- **AI-Powered Data Analysis**: Uses CrewAI agents to analyze datasets and generate insights
- **Parallel Processing**: Leverages Ray for distributed computing and parallel insight processing
- **Flexible Output Formats**: Supports both Markdown (human-readable) and JSON (agent-to-agent) output formats
- **Web Interface**: Provides a user-friendly web interface for selecting datasets and output formats

## Usage

### Web Interface

1. Select a dataset from the dropdown menu
2. Choose an output format:
   - **Markdown**: Human-readable format with headers, lists, and formatting (default)
   - **JSON**: Machine-readable format for agent-to-agent interactions
3. Click "Run Analysis" to start the flow

### Programmatic Usage

```python
from workflows.crewai_flow.main import kickoff
import asyncio

# Run with default parameters (sales_data dataset, markdown output)
result = asyncio.run(kickoff({}))

# Run with custom parameters
result = asyncio.run(kickoff({
    "dataset_name": "customer_feedback",
    "output_format": "json"
}))
```

## Output Formats

### Markdown Format

The Markdown format is designed for human readability and includes:

- Formatted headers for sections
- Bulleted lists for insights and recommendations
- Emphasis on important information
- Timestamp and dataset information

Example:
```markdown
# Analysis Results for Quarterly Sales Data

*Analysis completed at: 2023-06-15 14:30:45*

## Summary

The quarterly sales data shows a consistent growth trend across all regions...

## Key Insights (Prioritized)

1. **Electronics sales in the West region showed the highest growth in Q4** *(Priority: 9)*
2. **North region consistently outperforms other regions** *(Priority: 8)*
3. **Furniture sales are declining in all regions except South** *(Priority: 7)*

## Recommendations

1. Increase marketing budget for Electronics in the West region
2. Investigate reasons for furniture sales decline
3. Replicate North region strategies in other regions
```

### JSON Format

The JSON format is designed for machine readability and agent-to-agent interactions:

```json
{
  "summary": "The quarterly sales data shows a consistent growth trend across all regions...",
  "prioritized_insights": [
    {
      "insight": "Electronics sales in the West region showed the highest growth in Q4",
      "priority": 9,
      "processed_by": "Worker-2",
      "timestamp": "2023-06-15 14:30:40"
    },
    ...
  ],
  "recommendations": [
    "Increase marketing budget for Electronics in the West region",
    "Investigate reasons for furniture sales decline",
    "Replicate North region strategies in other regions"
  ],
  "dataset_analyzed": "sales_data",
  "timestamp": "2023-06-15 14:30:45"
}
```

## Integration with Kodosumi

This workflow is designed to work seamlessly with Kodosumi. When running in the Kodosumi environment:

- Ray initialization is handled automatically
- The web interface is accessible through the Kodosumi UI
- Results are displayed in the Kodosumi output panel

By default, the workflow uses the Markdown output format when running in Kodosumi, as this provides the best user experience in the Kodosumi interface.

## For AI Agents

If you are an AI agent interacting with this workflow programmatically, follow these guidelines:

### Output Format Selection

Always specify `output_format="json"` when calling this workflow to receive structured data that is easier to parse and process:

```python
# Example for AI agent integration
from workflows.crewai_flow.main import kickoff
import asyncio
import json

# Request JSON format for agent-to-agent interaction
result = asyncio.run(kickoff({
    "dataset_name": "sales_data",
    "output_format": "json"
}))

# Process the structured data
summary = result["summary"]
insights = [insight["insight"] for insight in result["prioritized_insights"]]
recommendations = result["recommendations"]

# Take action based on the insights
for insight in insights:
    if "high priority" in insight.lower():
        # Process high priority insights
        pass
```

### API Integration

When making HTTP requests to the workflow's API endpoint:

```bash
# Example curl request for AI agent integration
curl -X POST "http://localhost:8000/" \
  -d "dataset_name=sales_data&output_format=json"
```

### Error Handling

The workflow will validate all inputs and use defaults if invalid values are provided:
- Invalid dataset_name → defaults to "sales_data"
- Invalid output_format → defaults to "markdown"

Always check the response structure to ensure you received the expected format. 