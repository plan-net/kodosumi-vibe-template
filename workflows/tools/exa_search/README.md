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
results = exa_search_tool.run("latest AI advancements")
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
results = exa_search_tool.run(
    query="climate change solutions",
    summary_query="summarize the latest climate change solutions",
    num_results=5,
    include_domains=["nature.com", "science.org"],
    exclude_domains=["wikipedia.org"],
    search_type="keyword",
    max_chars=1000,
    livecrawl="always"
)
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

## Command Line Example

This package includes a command-line example script that demonstrates how to use the ExaSearchTool:

```bash
# Basic search
python workflows/tools/exa_search/example.py "latest AI research"

# Advanced search with parameters
python workflows/tools/exa_search/example.py "climate change solutions" \
    --summary "summarize recent climate solutions" \
    --results 3 \
    --include nature.com science.org \
    --exclude wikipedia.org \
    --type keyword \
    --chars 1000 \
    --livecrawl always \
    --debug
```

The `--debug` flag will print the raw JSON response from the API for troubleshooting.

## API Reference

### ExaSearchTool

The main tool class for performing web searches using Exa.ai.

**Parameters:**

- `api_key` (Optional[str]): Custom API key (defaults to `EXA_API_KEY` environment variable)
- `timeout` (Union[int, float]): Request timeout in seconds (default: 15)
- `max_retries` (int): Maximum retries for failed requests (default: 2)
- `retry_delay` (Union[int, float]): Delay between retries in seconds (default: 2)

**Input Parameters (for `_run` method):**

- `query` (str): Search query to run against Exa.ai
- `summary_query` (Optional[str]): Query to use for generating summaries of results
- `num_results` (int): Number of search results to return (default: 5)
- `include_domains` (Optional[List[str]]): Filter results to these domains
- `exclude_domains` (Optional[List[str]]): Exclude results from these domains
- `search_type` (str): Type of search to perform (default: "keyword")
- `max_chars` (int): Maximum characters to return for each result's content (default: 500)
- `livecrawl` (Optional[str]): Livecrawl setting ("always", "fallback", or "never")

### ExaSearchInput

Pydantic model that defines the input schema for the ExaSearchTool.

## Testing

Run the tests with:

```bash
# Run all tests
pytest tests/tools/exa_search/test_tool.py

# Run tests with verbose output
pytest tests/tools/exa_search/test_tool.py -v

# Run tests with coverage
pytest tests/tools/exa_search/test_tool.py --cov=workflows.tools.exa_search
``` 