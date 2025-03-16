"""
Unit tests for the processors module.
"""

import unittest
from unittest.mock import MagicMock, patch, call, ANY
import time
from typing import List, Dict, Any
from workflows.crewai_flow.processors import (
    process_with_ray_or_locally, _process_with_ray, _process_locally,
    create_fallback_response, handle_flow_error
)


class TestProcessors(unittest.TestCase):
    """Test cases for the processors module."""

    def setUp(self):
        """Set up test fixtures."""
        # Define a simple processing function for testing
        self.process_func = lambda item, index: {"item": item, "index": index, "processed": True}
        
        # Define a list of test items
        self.test_items = ["item1", "item2", "item3"]
        
        # Define expected results for the test items
        self.expected_results = [
            {"item": "item1", "index": 0, "processed": True},
            {"item": "item2", "index": 1, "processed": True},
            {"item": "item3", "index": 2, "processed": True}
        ]

    @patch('workflows.crewai_flow.processors.test_ray_connectivity')
    def test_process_with_ray_or_locally_empty_list(self, mock_test_ray):
        """Test that process_with_ray_or_locally returns an empty list when given an empty list."""
        result = process_with_ray_or_locally([], self.process_func)
        self.assertEqual(result, [])
        # Verify that test_ray_connectivity was not called
        mock_test_ray.assert_not_called()

    @patch('workflows.crewai_flow.processors.test_ray_connectivity')
    @patch('workflows.crewai_flow.processors._process_with_ray')
    def test_process_with_ray_or_locally_ray_working(self, mock_process_with_ray, mock_test_ray):
        """Test that process_with_ray_or_locally uses Ray when it's working."""
        # Configure the mock to indicate that Ray is working
        mock_test_ray.return_value = (True, "Ray is working")
        
        # Configure the mock to return expected results
        mock_process_with_ray.return_value = self.expected_results
        
        # Call the function
        result = process_with_ray_or_locally(self.test_items, self.process_func)
        
        # Verify the result
        self.assertEqual(result, self.expected_results)
        
        # Verify that test_ray_connectivity was called
        mock_test_ray.assert_called_once()
        
        # Verify that _process_with_ray was called with the correct arguments
        mock_process_with_ray.assert_called_once_with(self.test_items, self.process_func, 1)

    @patch('workflows.crewai_flow.processors.test_ray_connectivity')
    @patch('workflows.crewai_flow.processors._process_locally')
    def test_process_with_ray_or_locally_ray_not_working(self, mock_process_locally, mock_test_ray):
        """Test that process_with_ray_or_locally falls back to local processing when Ray is not working."""
        # Configure the mock to indicate that Ray is not working
        mock_test_ray.return_value = (False, None)
        
        # Configure the mock to return expected results
        mock_process_locally.return_value = self.expected_results
        
        # Call the function
        result = process_with_ray_or_locally(self.test_items, self.process_func)
        
        # Verify the result
        self.assertEqual(result, self.expected_results)
        
        # Verify that test_ray_connectivity was called
        mock_test_ray.assert_called_once()
        
        # Verify that _process_locally was called with the correct arguments
        mock_process_locally.assert_called_once_with(self.test_items, self.process_func)

    def test_process_locally(self):
        """Test that _process_locally correctly processes items."""
        result = _process_locally(self.test_items, self.process_func)
        self.assertEqual(result, self.expected_results)

    @patch('ray.remote')
    @patch('ray.get')
    def test_process_with_ray(self, mock_ray_get, mock_ray_remote):
        """Test that _process_with_ray correctly processes items using Ray."""
        # Configure the mocks
        mock_ray_remote.return_value = MagicMock()
        mock_ray_remote.return_value.remote.side_effect = lambda item, index: f"task_{item}_{index}"
        mock_ray_get.return_value = self.expected_results
        
        # Call the function
        with patch('ray.is_initialized', return_value=True):
            result = _process_with_ray(self.test_items, self.process_func, batch_size=3)
        
        # Verify the result
        self.assertEqual(result, self.expected_results)
        
        # Verify that ray.remote was called
        mock_ray_remote.assert_called_once()
        
        # Verify that ray.get was called with ANY list of tasks and the correct timeout
        mock_ray_get.assert_called_once_with(ANY, timeout=10.0)

    @patch('ray.remote')
    @patch('ray.get')
    def test_process_with_ray_timeout(self, mock_ray_get, mock_ray_remote):
        """Test that _process_with_ray falls back to local processing when Ray times out."""
        # Configure the mocks
        mock_ray_remote.return_value = MagicMock()
        mock_ray_remote.return_value.remote.side_effect = lambda item, index: f"task_{item}_{index}"
        mock_ray_get.side_effect = TimeoutError("Ray timed out")
        
        # Mock the process_func to track calls
        mock_process_func = MagicMock(side_effect=self.process_func)
        
        # Call the function
        with patch('ray.is_initialized', return_value=True):
            result = _process_with_ray(self.test_items, mock_process_func, batch_size=3)
        
        # Verify the result
        self.assertEqual(result, self.expected_results)
        
        # Verify that ray.remote was called
        mock_ray_remote.assert_called_once()
        
        # Verify that ray.get was called with ANY list of tasks and the correct timeout
        mock_ray_get.assert_called_once_with(ANY, timeout=10.0)
        
        # Verify that process_func was called for each item
        mock_process_func.assert_has_calls([
            call("item1", 0),
            call("item2", 1),
            call("item3", 2)
        ])

    def test_create_fallback_response(self):
        """Test that create_fallback_response creates the expected response."""
        # Call the function with a known dataset name
        result = create_fallback_response("sales_data")
        
        # Verify the structure of the result
        self.assertIn("analysis_results", result)
        self.assertIn("parallel_processing_results", result)
        self.assertIn("final_insights", result)
        
        # Verify the content of analysis_results
        analysis_results = result["analysis_results"]
        self.assertIn("summary", analysis_results)
        self.assertIn("Unable to analyze Quarterly Sales Data", analysis_results["summary"])
        self.assertIn("insights", analysis_results)
        self.assertIn("recommendations", analysis_results)
        
        # Verify the content of parallel_processing_results
        parallel_processing_results = result["parallel_processing_results"]
        self.assertEqual(len(parallel_processing_results), 1)
        self.assertIn("insight", parallel_processing_results[0])
        self.assertIn("priority", parallel_processing_results[0])
        self.assertEqual(parallel_processing_results[0]["priority"], 10)
        
        # Verify the content of final_insights
        final_insights = result["final_insights"]
        self.assertIn("summary", final_insights)
        self.assertIn("prioritized_insights", final_insights)
        self.assertIn("recommendations", final_insights)
        self.assertIn("dataset_analyzed", final_insights)
        self.assertEqual(final_insights["dataset_analyzed"], "sales_data")
        self.assertIn("timestamp", final_insights)

    def test_create_fallback_response_unknown_dataset(self):
        """Test that create_fallback_response handles unknown dataset names."""
        # Call the function with an unknown dataset name
        result = create_fallback_response("unknown_dataset")
        
        # Verify that the function still returns a valid response
        self.assertIn("analysis_results", result)
        self.assertIn("parallel_processing_results", result)
        self.assertIn("final_insights", result)
        
        # Verify that the dataset name is preserved
        self.assertEqual(result["final_insights"]["dataset_analyzed"], "unknown_dataset")

    @patch('workflows.crewai_flow.processors.create_fallback_response')
    @patch('workflows.crewai_flow.processors.format_output')
    def test_handle_flow_error(self, mock_format_output, mock_create_fallback_response):
        """Test that handle_flow_error correctly handles errors."""
        # Create a mock flow state
        mock_flow_state = MagicMock()
        mock_flow_state.dataset_name = "test_dataset"
        
        # Configure the mocks
        mock_fallback_data = {
            "analysis_results": {"summary": "Error summary"},
            "parallel_processing_results": [{"insight": "Error insight", "priority": 10}],
            "final_insights": {"summary": "Error summary", "dataset_analyzed": "test_dataset"}
        }
        mock_create_fallback_response.return_value = mock_fallback_data
        mock_format_output.return_value = "Formatted error output"
        
        # Call the function
        result = handle_flow_error(mock_flow_state, "markdown")
        
        # Verify the result
        self.assertEqual(result, "Formatted error output")
        
        # Verify that create_fallback_response was called with the correct arguments
        mock_create_fallback_response.assert_called_once_with("test_dataset")
        
        # Verify that format_output was called with the correct arguments
        mock_format_output.assert_called_once_with(mock_fallback_data["final_insights"], "markdown")
        
        # Verify that the flow state was updated
        self.assertEqual(mock_flow_state.analysis_results, mock_fallback_data["analysis_results"])
        self.assertEqual(mock_flow_state.parallel_processing_results, mock_fallback_data["parallel_processing_results"])
        self.assertEqual(mock_flow_state.final_insights, mock_fallback_data["final_insights"])


if __name__ == "__main__":
    unittest.main() 