"""
Tests for ExaSearchTool.
"""

import os
import json
import pytest
import requests
from unittest.mock import patch, MagicMock
from workflows.tools.exa_search import ExaSearchTool, ExaSearchInput

@pytest.fixture
def mock_env(monkeypatch):
    """Set up a mock environment with EXA_API_KEY."""
    monkeypatch.setenv("EXA_API_KEY", "test-api-key-12345")
    yield
    
@pytest.fixture
def mock_response():
    """Create a mock response for the API."""
    return {
        "results": [
            {
                "title": "Test Result 1",
                "url": "https://example.com/1",
                "text": "This is sample text content for test result 1.",
                "summary": "Summary of test result 1."
            },
            {
                "title": "Test Result 2",
                "url": "https://example.com/2",
                "text": "This is sample text content for test result 2.",
                "summary": "Summary of test result 2."
            }
        ]
    }

@pytest.fixture
def mock_requests(mock_response):
    """Create a mock for the requests library."""
    with patch('workflows.tools.exa_search.tool.requests') as mock_req:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status.return_value = None
        mock_req.post.return_value = mock_resp
        yield mock_req

def test_initialization_without_api_key():
    """Test initialization without an API key."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="EXA_API_KEY environment variable not set"):
            ExaSearchTool()

def test_initialization_with_api_key_from_env(mock_env):
    """Test initialization with API key from environment."""
    tool = ExaSearchTool()
    assert tool.api_key == "test-api-key-12345"
    assert tool.timeout == 15
    assert tool.max_retries == 2
    assert tool.retry_delay == 2
    assert tool.name == "exa_search"
    assert "Search the web" in tool.description

def test_initialization_with_custom_api_key():
    """Test initialization with a custom API key."""
    tool = ExaSearchTool(api_key="custom-api-key")
    assert tool.api_key == "custom-api-key"

def test_initialization_with_custom_parameters():
    """Test initialization with custom parameters."""
    tool = ExaSearchTool(
        api_key="custom-api-key",
        timeout=30,
        max_retries=5,
        retry_delay=1
    )
    assert tool.api_key == "custom-api-key"
    assert tool.timeout == 30
    assert tool.max_retries == 5
    assert tool.retry_delay == 1

def test_search_basic(mock_env, mock_requests, mock_response):
    """Test basic search functionality."""
    tool = ExaSearchTool()
    results = tool._search(
        query="test query",
        summary_query="test summary query"
    )
    
    # Check if API was called with correct parameters
    mock_requests.post.assert_called_once()
    args, kwargs = mock_requests.post.call_args
    assert args[0] == "https://api.exa.ai/search"
    assert kwargs["headers"]["Authorization"] == "Bearer test-api-key-12345"
    assert kwargs["headers"]["Content-Type"] == "application/json"
    assert kwargs["timeout"] == 15
    
    # Check payload
    payload = kwargs["json"]
    assert payload["query"] == "test query"
    assert payload["numResults"] == 5
    assert payload["type"] == "keyword"
    assert payload["contents"]["text"] is True
    assert payload["contents"]["summary"]["query"] == "test summary query"
    
    # Check results
    assert results == mock_response

def test_search_with_custom_parameters(mock_env, mock_requests, mock_response):
    """Test search with custom parameters."""
    tool = ExaSearchTool()
    results = tool._search(
        query="test query",
        summary_query="test summary query",
        num_results=10,
        include_domains=["example.com"],
        exclude_domains=["excluded.com"],
        search_type="neural",
        max_chars=1000,
        livecrawl="always"
    )
    
    # Check payload with custom parameters
    payload = mock_requests.post.call_args[1]["json"]
    assert payload["query"] == "test query"
    assert payload["numResults"] == 10
    assert payload["type"] == "neural"
    assert payload["includeDomains"] == ["example.com"]
    assert payload["excludeDomains"] == ["excluded.com"]
    assert payload["contents"]["text"] is True
    assert payload["contents"]["summary"]["query"] == "test summary query"
    assert payload["contents"]["livecrawl"] == "always"

def test_run_method_formatting(mock_env, mock_requests, mock_response):
    """Test that the _run method formats results correctly."""
    tool = ExaSearchTool()
    formatted_results = tool._run(
        query="test query",
        summary_query="test summary query"
    )
    
    # Check formatting
    assert isinstance(formatted_results, str)
    assert "Search Results for 'test query':" in formatted_results
    assert "[1] Test Result 1" in formatted_results
    assert "URL: https://example.com/1" in formatted_results
    assert "Content: This is sample text content for test result 1." in formatted_results
    assert "Summary: Summary of test result 1." in formatted_results
    
    assert "[2] Test Result 2" in formatted_results
    assert "URL: https://example.com/2" in formatted_results

def test_request_exception_handling(mock_env, mock_requests):
    """Test handling of request exceptions."""
    # Configure mock to raise an exception
    mock_requests.post.side_effect = requests.exceptions.RequestException("Test error")
    
    tool = ExaSearchTool(max_retries=1, retry_delay=0.1)
    
    with pytest.raises(ValueError, match="Exa search request failed:"):
        tool._search(query="test query", summary_query="test summary")
    
    # Should have been called twice (initial + 1 retry)
    assert mock_requests.post.call_count == 2

def test_timeout_exception_handling(mock_env, mock_requests):
    """Test handling of timeout exceptions."""
    # Configure mock to raise a timeout
    mock_requests.post.side_effect = requests.exceptions.Timeout("Test timeout")
    
    tool = ExaSearchTool(max_retries=1, retry_delay=0.1)
    
    with pytest.raises(ValueError, match="Exa search request timed out"):
        tool._search(query="test query", summary_query="test summary")
    
    # Should have been called twice (initial + 1 retry)
    assert mock_requests.post.call_count == 2 