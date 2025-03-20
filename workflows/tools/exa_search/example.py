#!/usr/bin/env python
"""
ExaSearchTool Example

This script demonstrates how to use the ExaSearchTool for web searching with Exa.ai.
"""

import os
import json
from dotenv import load_dotenv
import argparse
from workflows.tools.exa_search.tool import ExaSearchTool

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="ExaSearchTool example")
    parser.add_argument("query", help="The search query to run")
    parser.add_argument("--summary", help="Custom query for summary generation")
    parser.add_argument("--results", type=int, default=5, help="Number of results to return")
    parser.add_argument("--include", nargs="*", help="Domains to include in search results")
    parser.add_argument("--exclude", nargs="*", help="Domains to exclude from search results")
    parser.add_argument("--type", default="keyword", help="Search type (keyword, neural, etc.)")
    parser.add_argument("--chars", type=int, default=500, help="Max characters per result")
    parser.add_argument("--livecrawl", choices=["always", "fallback", "never"], 
                        help="Livecrawl setting")
    parser.add_argument("--debug", action="store_true", help="Print raw API response for debugging")
    args = parser.parse_args()
    
    # Load environment variables for API key
    load_dotenv()
    api_key = os.getenv("EXA_API_KEY")
    
    if not api_key:
        print("Error: EXA_API_KEY not found in environment variables.")
        print("Please set it in your .env file or export it in your shell.")
        return
    
    try:
        # Initialize the ExaSearchTool
        tool = ExaSearchTool(api_key=api_key)
        
        # Get raw search results first if debug is enabled
        if args.debug:
            raw_results = tool._search(
                query=args.query,
                summary_query=args.summary or args.query,
                num_results=args.results,
                include_domains=args.include,
                exclude_domains=args.exclude,
                search_type=args.type,
                max_chars=args.chars,
                livecrawl=args.livecrawl
            )
            print("\n" + "="*80)
            print("RAW API RESPONSE:")
            print(json.dumps(raw_results, indent=2))
            print("="*80 + "\n")
        
        # Run the search for formatted results
        formatted_results = tool._run(
            query=args.query,
            summary_query=args.summary,
            num_results=args.results,
            include_domains=args.include,
            exclude_domains=args.exclude,
            search_type=args.type,
            max_chars=args.chars,
            livecrawl=args.livecrawl
        )
        
        # Print the formatted results
        print("\n" + "="*80)
        print("FORMATTED RESULTS:")
        print(formatted_results)
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    main() 