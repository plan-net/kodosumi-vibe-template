"""
Unit tests for the processors module.
"""

import unittest
from unittest.mock import MagicMock, patch, ANY
import time
from typing import List, Dict, Any
import ray
import pytest

from workflows.common.processors import (
    process_with_ray_or_locally,
    _process_with_ray,
    _process_locally,
    create_fallback_response,
    handle_flow_error
)
from workflows.common.utils import (
    RAY_TASK_NUM_CPUS,
    RAY_TASK_MAX_RETRIES,
    RAY_TASK_TIMEOUT,
    RAY_BATCH_SIZE,
    test_ray_connectivity
)

class TestProcessors(unittest.TestCase):
    """Test cases for the processors module."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_items = ["item1", "item2", "item3"]
        self.process_func = lambda x, i: f"processed_{x}"
        self.expected_results = ["processed_item1", "processed_item2", "processed_item3"]
    
    @patch('workflows.common.processors.test_ray_connectivity')
    @patch('workflows.common.processors._process_with_ray')
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
        mock_process_with_ray.assert_called_once_with(
            self.test_items,
            self.process_func,
            RAY_BATCH_SIZE
        )
    
    @patch('workflows.common.processors.test_ray_connectivity')
    @patch('workflows.common.processors._process_locally')
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
        mock_process_locally.assert_called_once_with(
            self.test_items,
            self.process_func
        )
    
    def test_process_with_ray_or_locally_empty_list(self):
        """Test that process_with_ray_or_locally handles empty lists correctly."""
        result = process_with_ray_or_locally([], self.process_func)
        self.assertEqual(result, [])
    
    @patch('ray.remote')
    @patch('ray.get')
    def test_process_with_ray(self, mock_ray_get, mock_ray_remote):
        """Test that _process_with_ray processes items correctly."""
        # Configure the mocks
        mock_ray_remote.return_value = MagicMock()
        mock_ray_remote.return_value.remote.return_value = "remote_task"
        mock_ray_get.return_value = self.expected_results[:1]  # Return one result at a time
        
        # Call the function
        result = _process_with_ray(self.test_items[:1], self.process_func)  # Process one item
        
        # Verify the result
        self.assertEqual(result, self.expected_results[:1])
        
        # Verify that ray.remote was called with the correct arguments
        mock_ray_remote.assert_called_once_with(num_cpus=RAY_TASK_NUM_CPUS, max_retries=RAY_TASK_MAX_RETRIES)
    
    @patch('ray.remote')
    @patch('ray.get')
    def test_process_with_ray_timeout(self, mock_ray_get, mock_ray_remote):
        """Test that _process_with_ray handles timeouts correctly."""
        # Configure the mocks
        mock_ray_remote.return_value = MagicMock()
        mock_ray_remote.return_value.remote.return_value = "remote_task"
        mock_ray_get.side_effect = TimeoutError("Ray timed out")
        
        # Call the function
        result = _process_with_ray(self.test_items[:1], self.process_func)  # Process one item
        
        # Verify that we got a result (processed locally after timeout)
        self.assertEqual(result, self.expected_results[:1])
    
    def test_process_locally(self):
        """Test that _process_locally processes items correctly."""
        result = _process_locally(self.test_items, self.process_func)
        self.assertEqual(result, self.expected_results)
    
    def test_create_fallback_response(self):
        """Test that create_fallback_response creates the expected response."""
        # Call the function with a known dataset name
        result = create_fallback_response("test_dataset")
        
        # Verify the structure of the result
        self.assertIn("analysis_results", result)
        self.assertIn("parallel_processing_results", result)
        self.assertIn("final_insights", result)
        
        # Verify the content of analysis_results
        analysis_results = result["analysis_results"]
        self.assertIn("summary", analysis_results)
        self.assertIn("Unable to analyze test_dataset", analysis_results["summary"])
        self.assertIn("insights", analysis_results)
        self.assertIn("recommendations", analysis_results)
    
    def test_create_fallback_response_unknown_dataset(self):
        """Test that create_fallback_response handles unknown datasets correctly."""
        result = create_fallback_response("unknown_dataset")
        self.assertIn("analysis_results", result)
        self.assertIn("Unable to analyze unknown_dataset", result["analysis_results"]["summary"])
    
    @patch('workflows.common.processors.format_output')
    def test_handle_flow_error(self, mock_format_output):
        """Test that handle_flow_error correctly handles errors."""
        # Create a mock flow state
        mock_flow_state = MagicMock()
        mock_flow_state.dataset_name = "test_dataset"
        
        # Configure the mock
        mock_format_output.return_value = "Formatted error output"
        
        # Call the function
        result = handle_flow_error(mock_flow_state, "markdown")
        
        # Verify the result
        self.assertEqual(result, "Formatted error output")
        
        # Verify that format_output was called with the correct arguments
        mock_format_output.assert_called_once()
        args = mock_format_output.call_args[0]
        self.assertIsInstance(args[0], dict)  # First arg should be the insights dict
        self.assertEqual(args[1], "markdown")  # Second arg should be the output format


if __name__ == "__main__":
    unittest.main() 