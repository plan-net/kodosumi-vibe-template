"""
Unit tests for the formatters module.
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import json
import time
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from workflows.common.formatters import (
    format_output,
    format_as_markdown,
    extract_structured_data,
    format_dict_item,
    pydantic_to_markdown_template
)


class SampleModel(BaseModel):
    """Sample Pydantic model for testing."""
    title: str = "Test Report"
    summary: str = "This is a test summary"
    insights: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    timestamp: str = "2023-01-01 12:00:00"


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
        
        self.sample_model = SampleModel(
            title="Test Report",
            summary="This is a test summary",
            insights=[
                {"insight": "Insight 1", "priority": 9},
                {"insight": "Insight 2", "priority": 7}
            ],
            recommendations=[
                "Recommendation 1",
                "Recommendation 2"
            ],
            timestamp="2023-01-01 12:00:00"
        )
        
        self.custom_template = {
            "title": "Custom Report",
            "sections": [
                {
                    "title": "Executive Summary",
                    "field": "summary",
                    "format": "text"
                },
                {
                    "title": "Key Findings",
                    "field": "prioritized_insights",
                    "format": "list",
                    "item_format": {
                        "main_field": "insight",
                        "additional_fields": ["priority"]
                    }
                },
                {
                    "title": "Action Items",
                    "field": "recommendations",
                    "format": "list"
                }
            ]
        }

    def test_format_output_json_dict(self):
        """Test that format_output returns the raw data when format is json."""
        result = format_output(self.sample_insights, "json")
        self.assertEqual(result, self.sample_insights)

    def test_format_output_json_model(self):
        """Test that format_output correctly handles Pydantic models with JSON format."""
        result = format_output(self.sample_model, "json")
        self.assertEqual(result, self.sample_model.model_dump())

    def test_format_output_markdown_dict(self):
        """Test that format_output correctly formats dictionary output in markdown."""
        result = format_output(self.sample_insights, "markdown")
        
        # Verify that the result contains markdown formatting
        self.assertIn("# Report", result)  # Default title
        
        # Verify content sections are generated
        self.assertIn("## Dataset Analyzed", result)
        self.assertIn("## Summary", result)
        self.assertIn("## Prioritized Insights", result)
        self.assertIn("## Recommendations", result)
        
        # Verify content
        self.assertIn("test_dataset", result)
        self.assertIn("This is a test summary", result)
        self.assertIn("Insight 1", result)
        self.assertIn("Recommendation 1", result)
        
        # Verify timestamp
        self.assertIn("*Generated on 2023-01-01 12:00:00*", result)

    def test_format_output_markdown_model(self):
        """Test that format_output correctly formats Pydantic model output in markdown."""
        result = format_output(self.sample_model, "markdown")
        
        # Verify that the result contains markdown formatting
        self.assertIn("# Test Report", result)  # Title from model
        
        # Verify content sections are generated
        self.assertIn("## Summary", result)
        self.assertIn("## Insights", result)
        self.assertIn("## Recommendations", result)
        
        # Verify content
        self.assertIn("This is a test summary", result)
        self.assertIn("Insight 1", result)
        self.assertIn("Recommendation 1", result)
        
        # Verify timestamp
        self.assertIn("*Generated on 2023-01-01 12:00:00*", result)

    def test_format_output_with_template(self):
        """Test that format_output correctly uses a custom template."""
        # Create a template with timestamp field properly set
        template = self.custom_template.copy()
        template["timestamp_field"] = "timestamp"
        template["include_timestamp"] = True
        
        result = format_output(self.sample_insights, "markdown", template)
        
        # Verify that the result contains custom template formatting
        self.assertIn("# Custom Report", result)
        
        # Verify expected section titles
        self.assertIn("## Summary", result)
        self.assertIn("## Prioritized Insights", result)
        self.assertIn("## Recommendations", result)
        
        # Verify content
        self.assertIn("This is a test summary", result)
        self.assertIn("Insight 1", result)
        self.assertIn("priority: 9", result)
        self.assertIn("Recommendation 1", result)

    def test_format_output_default(self):
        """Test that format_output defaults to markdown when no format is specified."""
        result = format_output(self.sample_insights)
        self.assertIsInstance(result, str)
        self.assertIn("# Report", result)

    def test_format_as_markdown_auto_sections(self):
        """Test that format_as_markdown correctly auto-generates sections."""
        result = format_as_markdown(self.sample_insights)
        
        # Check that the result is a string
        self.assertIsInstance(result, str)
        
        # Check that the markdown contains auto-generated sections
        self.assertIn("# Report", result)
        self.assertIn("## Dataset Analyzed", result)
        self.assertIn("## Summary", result)
        self.assertIn("## Prioritized Insights", result)
        self.assertIn("## Recommendations", result)
        
        # Check content
        self.assertIn("test_dataset", result)
        self.assertIn("This is a test summary", result)
        self.assertIn("*Generated on 2023-01-01 12:00:00*", result)

    def test_format_as_markdown_with_template(self):
        """Test that format_as_markdown correctly uses a template."""
        # Create a template with timestamp field properly set
        template = self.custom_template.copy()
        template["timestamp_field"] = "timestamp"
        template["include_timestamp"] = True
        
        result = format_as_markdown(self.sample_insights, template)
        
        # Check that the result is a string
        self.assertIsInstance(result, str)
        
        # Check that the markdown contains expected content
        self.assertIn("# Custom Report", result)
        self.assertIn("## Summary", result)
        self.assertIn("## Prioritized Insights", result)
        self.assertIn("## Recommendations", result)
        
        # Check content
        self.assertIn("This is a test summary", result)
        self.assertIn("Insight 1", result)
        self.assertIn("Recommendation 1", result)

    def test_format_dict_item(self):
        """Test that format_dict_item correctly formats dictionary items."""
        item = {"insight": "Test Insight", "priority": 8, "source": "Analysis"}
        item_format = {"main_field": "insight", "additional_fields": ["priority", "source"]}
        
        result = format_dict_item(item, item_format)
        
        self.assertEqual(result, "**Test Insight** (priority: 8, source: Analysis)")
        
        # Test with empty item_format
        result = format_dict_item(item, {})
        self.assertEqual(result, "**Test Insight**")

    def test_pydantic_to_markdown_template(self):
        """Test that pydantic_to_markdown_template correctly generates a template from a model."""
        template = pydantic_to_markdown_template(SampleModel)
        
        # Check template structure
        self.assertEqual(template["title"], "SampleModel")
        self.assertIsInstance(template["sections"], list)
        
        # Check that all fields are included
        field_names = [section["field"] for section in template["sections"]]
        self.assertIn("title", field_names)
        self.assertIn("summary", field_names)
        self.assertIn("insights", field_names)
        self.assertIn("recommendations", field_names)
        self.assertIn("timestamp", field_names)
        
        # Check format types
        for section in template["sections"]:
            if section["field"] == "insights":
                self.assertEqual(section["format"], "list")
            elif section["field"] == "recommendations":
                self.assertEqual(section["format"], "list")
            else:
                self.assertEqual(section["format"], "text")

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


if __name__ == "__main__":
    unittest.main() 