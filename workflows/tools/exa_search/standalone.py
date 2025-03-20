#!/usr/bin/env python
"""
Standalone example of the ExaSearchTool.

This script demonstrates how to use the ExaSearchTool directly,
without the CrewAI framework.
"""

import os
import json
from dotenv import load_dotenv
from workflows.tools.exa_search import ExaSearchTool

# Load environment variables (make sure EXA_API_KEY is set)
load_dotenv()

def main():
    """Run a simple standalone example of the ExaSearchTool."""
    
    # Check if API key is set
    if not os.getenv("EXA_API_KEY"):
        print("Error: EXA_API_KEY environment variable is not set.")
        print("Please set your API key in .env file or environment variables.")
        return
    
    print("ExaSearchTool Standalone Demo")
    print("=============================")
    
    # Create the tool with some custom parameters
    exa_tool = ExaSearchTool(
        timeout=20,
        max_retries=2,
        retry_delay=1
    )
    
    # Example 1: Basic search
    query = "What are the latest advancements in quantum computing?"
    print(f"\nExample 1: Basic search for '{query}'")
    print("-" * 40)
    
    try:
        results = exa_tool.run({"query": query})
        print(results)
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Search with parameters
    print("\nExample 2: Search with custom parameters")
    print("-" * 40)
    
    try:
        results = exa_tool.run({
            "query": "climate change solutions",
            "summary_query": "summarize the latest technological solutions for climate change",
            "num_results": 3,
            "max_chars": 500,
            "livecrawl": "auto"
        })
        print(results)
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 3: Domain filtering
    print("\nExample 3: Search with domain filtering")
    print("-" * 40)
    
    try:
        results = exa_tool.run({
            "query": "artificial intelligence ethics",
            "include_domains": ["stanford.edu", "mit.edu", "harvard.edu"],
            "num_results": 2
        })
        print(results)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 