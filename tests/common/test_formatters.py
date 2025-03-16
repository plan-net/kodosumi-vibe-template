"""
Unit tests for the formatters module.
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import json
import pytest

from workflows.common.formatters import (
    format_output,
    format_as_markdown,
    extract_structured_data
)


class TestFormatters(unittest.TestCase):
    """Test cases for the formatters module."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_insights = {
            "dataset_analyzed": "test_dataset",
            "timestamp": "2023-01-01 12:00:00",
            "summary": "This is a test summary",
            "prioritized_insights": [
                {"insight": "Insight 1", "priority": 9},
                {"insight": "Insight 2", "priority": 7}
            ],
            "recommendations": [
                "Recommendation 1",
                "Recommendation 2"
            ]
        }

    def test_format_output_json(self):
        """Test that format_output returns the raw data when format is json."""
        result = format_output(self.sample_insights, "json")
        self.assertEqual(result, self.sample_insights)

    def test_format_output_markdown(self):
        """Test that format_output correctly formats output in markdown."""
        result = format_output(self.sample_insights, "markdown")
        
        # Verify that the result contains markdown formatting
        self.assertIn("# Data Analysis Report", result)
        self.assertIn("## Summary", result)
        self.assertIn("## Key Insights", result)
        self.assertIn("## Recommendations", result)
        self.assertIn("*Generated on", result)
        
        # Verify content
        self.assertIn("test_dataset", result)
        self.assertIn("This is a test summary", result)
        self.assertIn("Insight 1", result)
        self.assertIn("Priority: 9", result)
        self.assertIn("Recommendation 1", result)

    def test_format_output_default(self):
        """Test that format_output defaults to markdown when no format is specified."""
        result = format_output(self.sample_insights)
        self.assertIsInstance(result, str)
        self.assertIn("# Data Analysis Report: test_dataset", result)

    def test_format_as_markdown(self):
        """Test that format_as_markdown correctly formats the insights as markdown."""
        result = format_as_markdown(self.sample_insights)
        
        # Check that the result is a string
        self.assertIsInstance(result, str)
        
        # Check that the markdown contains the expected sections
        self.assertIn("# Data Analysis Report: test_dataset", result)
        self.assertIn("## Summary", result)
        self.assertIn("This is a test summary", result)
        self.assertIn("## Key Insights", result)
        self.assertIn("1. **Insight 1** (Priority: 9)", result)
        self.assertIn("2. **Insight 2** (Priority: 7)", result)
        self.assertIn("## Recommendations", result)
        self.assertIn("1. Recommendation 1", result)
        self.assertIn("2. Recommendation 2", result)
        self.assertIn("*Generated on 2023-01-01 12:00:00*", result)

    def test_extract_structured_data_with_json_dict(self):
        """Test extract_structured_data when the task output has a json_dict attribute."""
        # Create a mock task output with a json_dict attribute
        mock_task = MagicMock()
        mock_task.json_dict = {"summary": "Test summary", "insights": ["Insight 1"]}
        
        # Create a mock crew result with the mock task
        mock_crew_result = MagicMock()
        mock_crew_result.tasks_output = [mock_task]
        
        result = extract_structured_data(mock_crew_result)
        
        self.assertEqual(result, {"summary": "Test summary", "insights": ["Insight 1"]})

    def test_extract_structured_data_with_raw_json(self):
        """Test extract_structured_data when the task output has a raw attribute with JSON."""
        # Create a mock task output with a raw attribute containing JSON
        mock_task = MagicMock()
        mock_task.json_dict = None
        mock_task.raw = '{"summary": "Test summary", "insights": ["Insight 1"]}'
        
        # Create a mock crew result with the mock task
        mock_crew_result = MagicMock()
        mock_crew_result.tasks_output = [mock_task]
        
        result = extract_structured_data(mock_crew_result)
        
        self.assertEqual(result, {"summary": "Test summary", "insights": ["Insight 1"]})

    def test_extract_structured_data_with_embedded_json(self):
        """Test extract_structured_data when the task output has a raw attribute with embedded JSON."""
        # Create a mock task output with a raw attribute containing embedded JSON
        mock_task = MagicMock()
        mock_task.json_dict = None
        mock_task.raw = 'Some text before {"summary": "Test summary", "insights": ["Insight 1"]} some text after'
        
        # Create a mock crew result with the mock task
        mock_crew_result = MagicMock()
        mock_crew_result.tasks_output = [mock_task]
        
        result = extract_structured_data(mock_crew_result)
        
        self.assertEqual(result, {"summary": "Test summary", "insights": ["Insight 1"]})

    def test_extract_structured_data_with_string_representation(self):
        """Test extract_structured_data when using string representation of the task."""
        # Create a mock task output with a string representation containing JSON
        mock_task = MagicMock()
        mock_task.json_dict = None
        mock_task.raw = None
        mock_task.__str__ = lambda self: 'Some text {"summary": "Test summary", "insights": ["Insight 1"]}'
        
        # Create a mock crew result with the mock task
        mock_crew_result = MagicMock()
        mock_crew_result.tasks_output = [mock_task]
        
        result = extract_structured_data(mock_crew_result)
        
        self.assertEqual(result, {"summary": "Test summary", "insights": ["Insight 1"]})

    def test_extract_structured_data_no_tasks_output(self):
        """Test extract_structured_data when there are no task outputs."""
        # Create a mock crew result with no task outputs
        mock_crew_result = MagicMock()
        mock_crew_result.tasks_output = []
        
        result = extract_structured_data(mock_crew_result)
        
        self.assertIsNone(result)

    def test_extract_structured_data_no_json(self):
        """Test extract_structured_data when there is no JSON in the task output."""
        # Create a mock task output with no JSON
        mock_task = MagicMock()
        mock_task.json_dict = None
        mock_task.raw = "This is not JSON"
        
        # Create a mock crew result with the mock task
        mock_crew_result = MagicMock()
        mock_crew_result.tasks_output = [mock_task]
        
        result = extract_structured_data(mock_crew_result)
        
        self.assertIsNone(result)

    def test_extract_structured_data_exception(self):
        """Test extract_structured_data when an exception occurs."""
        # Create a mock crew result that raises an exception when accessed
        mock_crew_result = MagicMock()
        # Configure the mock to raise an exception when tasks_output is accessed
        type(mock_crew_result).tasks_output = PropertyMock(side_effect=Exception("Test exception"))
        
        result = extract_structured_data(mock_crew_result)
        
        self.assertIsNone(result)

    def test_format_output_json(self):
        """Test that format_output correctly formats output in JSON."""
        result = format_output(self.sample_insights, "json")
        
        # Verify that we get back the same dictionary
        self.assertEqual(result, self.sample_insights)
    
    def test_format_output_invalid_format(self):
        """Test that format_output handles invalid output formats gracefully."""
        # Invalid formats should default to markdown
        result = format_output(self.sample_insights, "invalid_format")
        self.assertIn("# Data Analysis Report", result)


if __name__ == "__main__":
    unittest.main() 