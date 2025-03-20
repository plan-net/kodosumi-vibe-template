"""
Exa Search Tool implementation for CrewAI.

This module provides the ExaSearchTool class for searching the web using the Exa.ai API.
"""

import os
import json
import time
from typing import Optional, Type, List, Dict, Any, Union
import requests
from requests.exceptions import RequestException, Timeout
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ExaSearchInput(BaseModel):
    """Input schema for the Exa Search Tool."""
    query: str = Field(..., description="Search query to run against Exa.ai")
    summary_query: Optional[str] = Field(None, description="Query to use for generating summaries of results")
    num_results: int = Field(5, description="Number of search results to return")
    include_domains: Optional[List[str]] = Field(None, description="Filter results to these domains")
    exclude_domains: Optional[List[str]] = Field(None, description="Exclude results from these domains")
    search_type: str = Field("keyword", description="Type of search to perform (keyword, neural, etc.)")
    max_chars: int = Field(500, description="Maximum characters to return for each result's content")
    livecrawl: Optional[str] = Field(None, description="Livecrawl setting (always, fallback, or never)")

class ExaSearchTool(BaseTool):
    """
    A tool for searching the web using the Exa.ai API.
    
    This tool allows CrewAI agents to search the web for current and relevant
    information using the Exa.ai search API.
    """
    name: str = "exa_search"
    description: str = "Search the web for current information using Exa.ai API"
    args_schema: Type[BaseModel] = ExaSearchInput
    
    # Define fields as model attributes
    api_key: Optional[str] = Field(None, description="API key for Exa.ai")
    timeout: Union[int, float] = Field(15, description="Request timeout in seconds")
    max_retries: int = Field(2, description="Maximum retries for failed requests") 
    retry_delay: Union[int, float] = Field(2, description="Delay between retries in seconds")
    
    class Config:
        """Pydantic model configuration."""
        arbitrary_types_allowed = True
        extra = "allow"
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        timeout: Union[int, float] = 15, 
        max_retries: int = 2, 
        retry_delay: Union[int, float] = 2
    ):
        """
        Initialize the ExaSearchTool.
        
        Args:
            api_key: Optional Exa.ai API key (defaults to EXA_API_KEY env var)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        # Initialize with Pydantic model fields
        super().__init__(
            api_key=api_key or os.getenv("EXA_API_KEY"),
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        
        if not self.api_key:
            raise ValueError(
                "EXA_API_KEY environment variable not set. "
                "Please set it in your .env file or pass it directly to the constructor."
            )
    
    def _run(
        self, 
        query: str,
        summary_query: Optional[str] = None,
        num_results: int = 5,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        search_type: str = "keyword",
        max_chars: int = 500,
        livecrawl: Optional[str] = None
    ) -> str:
        """
        Run the Exa.ai search tool.
        
        Args:
            query: Search query
            summary_query: Query to use for generating summaries (defaults to same as query)
            num_results: Number of results to return
            include_domains: Optional list of domains to include
            exclude_domains: Optional list of domains to exclude
            search_type: Type of search to perform (keyword, neural, etc.)
            max_chars: Maximum characters to return for each result's content
            livecrawl: Livecrawl setting (always, fallback, or never)
            
        Returns:
            Formatted string containing search results
        """
        # Get raw results
        results = self._search(
            query=query,
            summary_query=summary_query or query,
            num_results=num_results,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
            search_type=search_type,
            max_chars=max_chars,
            livecrawl=livecrawl
        )
        
        # Format results as readable text for LLM consumption
        formatted_results = []
        for i, result in enumerate(results.get("results", []), 1):
            title = result.get("title", "No Title")
            url = result.get("url", "No URL")
            
            # Extract text content directly from the result
            content = result.get("text", "No content available")
            
            # Truncate content if needed
            if content and len(content) > max_chars:
                content = content[:max_chars] + "..."
            
            # Add summary if available
            summary = ""
            if "summary" in result:
                summary = f"\nSummary: {result['summary']}"
            
            formatted_results.append(f"[{i}] {title}\nURL: {url}\nContent: {content}{summary}\n")
        
        if formatted_results:
            return "\n".join([
                f"Search Results for '{query}':",
                "\n".join(formatted_results)
            ])
        else:
            return f"No results found for '{query}'"
    
    def _search(
        self, 
        query: str,
        summary_query: str,
        num_results: int = 5,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        search_type: str = "keyword",
        max_chars: int = 500,
        livecrawl: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform web search using Exa.ai API.
        
        Args:
            query: Search query
            summary_query: Query to use for generating summaries
            num_results: Number of results to return
            include_domains: Optional list of domains to include
            exclude_domains: Optional list of domains to exclude
            search_type: Type of search to perform (keyword, neural, etc.)
            max_chars: Maximum characters to return for each result
            livecrawl: Livecrawl setting (always, fallback, or never)
            
        Returns:
            Raw response from Exa.ai API
        """
        url = "https://api.exa.ai/search"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Build the request payload
        payload = {
            "query": query,
            "numResults": num_results,
            "type": search_type
        }
        
        # Configure contents based on the example
        contents = {
            "text": True
        }
        
        # Add summary if requested
        if summary_query:
            contents["summary"] = {"query": summary_query}
            
        # Add livecrawl if specified
        if livecrawl:
            contents["livecrawl"] = livecrawl
            
        payload["contents"] = contents
        
        # Add domain filters if provided
        if include_domains:
            payload["includeDomains"] = include_domains
        if exclude_domains:
            payload["excludeDomains"] = exclude_domains
        
        # Retry logic
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    url, 
                    json=payload, 
                    headers=headers, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            except Timeout:
                if attempt < self.max_retries:
                    print(f"Request timed out. Retry {attempt+1}/{self.max_retries}...")
                    time.sleep(self.retry_delay)
                else:
                    raise ValueError(f"Exa search request timed out after {self.max_retries + 1} attempts")
            except RequestException as e:
                if attempt < self.max_retries:
                    print(f"Request failed with error: {str(e)}. Retry {attempt+1}/{self.max_retries}...")
                    time.sleep(self.retry_delay)
                else:
                    status_code = getattr(e.response, 'status_code', None)
                    error_msg = f"Exa search request failed: {str(e)}"
                    
                    # Try to get more detailed error message from response
                    try:
                        error_detail = e.response.json()
                        error_msg += f" Details: {json.dumps(error_detail)}"
                    except:
                        pass
                        
                    raise ValueError(error_msg) 