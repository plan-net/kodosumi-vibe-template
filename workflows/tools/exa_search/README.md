# Exa Search Tool for CrewAI

This package provides a tool for searching the web using the [Exa.ai](https://exa.ai) API as part of CrewAI workflows.

## Features

- Search the web for up-to-date information
- Optional summarization of search results
- Domain filtering (include or exclude specific domains)
- Live crawling for fresh results
- Configurable result limits and content length
- Built-in retry mechanism for failed requests

## Setup

1. Sign up for an API key at [Exa.ai](https://exa.ai)
2. Set your API key in your environment variables:
   ```
   EXA_API_KEY=your_api_key_here
   ```
   Or use a `.env` file with `python-dotenv`

## Usage

### Basic usage

```python
from workflows.tools.exa_search import ExaSearchTool

# Create the tool
exa_search_tool = ExaSearchTool()

# Use the tool directly
results = exa_search_tool.run({"query": "latest AI advancements"})
print(results)
```

### With custom parameters

```python
exa_search_tool = ExaSearchTool(
    timeout=15,            # Request timeout in seconds
    max_retries=3,         # Maximum retries for failed requests
    retry_delay=2,         # Delay between retries in seconds
    api_key="your_key"     # Override environment variable
)

# Search with additional parameters
results = exa_search_tool.run({
    "query": "climate change solutions",
    "summary_query": "summarize the latest climate change solutions",
    "num_results": 5,
    "include_domains": ["nature.com", "science.org"],
    "exclude_domains": ["wikipedia.org"],
    "search_type": "keyword",
    "max_chars": 1000,
    "livecrawl": "always"
})
```

## Using with CrewAI

The `ExaSearchTool` can be easily integrated with CrewAI agents:

```python
from crewai import Agent
from workflows.tools.exa_search import ExaSearchTool

# Create the tool
exa_search_tool = ExaSearchTool()

# Create an agent with the tool
researcher = Agent(
    role="Research Specialist",
    goal="Find accurate information on topics",
    backstory="You are a skilled researcher with expertise in finding information.",
    tools=[exa_search_tool],
    verbose=True
)
```

## Examples

This package includes two example scripts:

1. `standalone.py` - Demonstrates using the ExaSearchTool directly without CrewAI
2. `crewai_example.py` - Shows how to use the ExaSearchTool in a CrewAI workflow

To run the examples:

```bash
# Run the standalone example
python -m workflows.tools.exa_search.standalone

# Run the CrewAI example
python -m workflows.tools.exa_search.crewai_example
```

## API Reference

### ExaSearchTool

The main tool class for performing web searches using Exa.ai.

**Parameters:**

- `api_key` (Optional): Custom API key (defaults to `EXA_API_KEY` environment variable)
- `timeout` (int): Request timeout in seconds (default: 15)
- `max_retries` (int): Maximum retries for failed requests (default: 2)
- `retry_delay` (int): Delay between retries in seconds (default: 2)

**Input Parameters (for `run` method):**

- `query` (str): Search query to run against Exa.ai
- `summary_query` (str, optional): Query to use for generating summaries of results
- `num_results` (int): Number of search results to return (default: 5)
- `include_domains` (List[str], optional): Filter results to these domains
- `exclude_domains` (List[str], optional): Exclude results from these domains
- `search_type` (str): Type of search to perform (default: "keyword")
- `max_chars` (int): Maximum characters to return for each result's content (default: 500)
- `livecrawl` (str, optional): Livecrawl setting ("always", "fallback", or "never") 