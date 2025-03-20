# Custom Tools for CrewAI

This directory contains custom tools for use with CrewAI workflows.

## Available Tools

### ExaSearchTool

The `ExaSearchTool` provides web search functionality using the [Exa.ai](https://exa.ai) API.

#### Features

- Search the web for up-to-date information
- Optional summarization of search results
- Domain filtering (include or exclude specific domains)
- Live crawling for fresh results
- Configurable result limits and content length
- Built-in retry mechanism for failed requests

#### Setup

1. Sign up for an API key at [Exa.ai](https://exa.ai)
2. Set your API key in your environment variables:
   ```
   EXA_API_KEY=your_api_key_here
   ```
   Or use a `.env` file with `python-dotenv`

#### Usage

Basic usage:

```python
from workflows.tools.exa_search import ExaSearchTool

# Create the tool
exa_search_tool = ExaSearchTool()

# Use the tool directly
results = exa_search_tool.run({"query": "latest AI advancements"})
print(results)
```

With custom parameters:

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

#### Using with CrewAI

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

See `exa_example.py` for a complete example of using the `ExaSearchTool` in a CrewAI workflow.

### ExampleTool

A simple example tool demonstrating the basic structure of a CrewAI tool.

## Creating Custom Tools

To create a new tool:

1. Create a new Python file in this directory
2. Define your tool class extending `BaseTool` from LangChain
3. Implement the required methods: `_run` and `_arun`
4. Import and add your tool to `__init__.py`

See `example_tool.py` for a simple example of creating a custom tool. 