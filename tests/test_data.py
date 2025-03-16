"""
Unit tests for the data module.
"""

import unittest
from workflows.crewai_flow.data import SAMPLE_DATASETS


class TestData(unittest.TestCase):
    """Test cases for the data module."""

    def test_sample_datasets_structure(self):
        """Test that SAMPLE_DATASETS has the expected structure."""
        # Check that SAMPLE_DATASETS is a dictionary
        self.assertIsInstance(SAMPLE_DATASETS, dict)
        
        # Check that it contains the expected datasets
        self.assertIn("sales_data", SAMPLE_DATASETS)
        self.assertIn("customer_feedback", SAMPLE_DATASETS)
        
        # Check that each dataset has the expected keys
        for dataset_name, dataset in SAMPLE_DATASETS.items():
            self.assertIn("name", dataset)
            self.assertIn("description", dataset)
            self.assertIn("sample", dataset)
            
            # Check that sample is a list
            self.assertIsInstance(dataset["sample"], list)
            
            # Check that sample is not empty
            self.assertGreater(len(dataset["sample"]), 0)

    def test_sales_data_structure(self):
        """Test the structure of the sales_data dataset."""
        sales_data = SAMPLE_DATASETS["sales_data"]
        
        # Check the name and description
        self.assertEqual(sales_data["name"], "Quarterly Sales Data")
        self.assertIn("Sales data", sales_data["description"])
        
        # Check the sample data structure
        sample = sales_data["sample"]
        for item in sample:
            self.assertIn("quarter", item)
            self.assertIn("region", item)
            self.assertIn("category", item)
            self.assertIn("sales", item)
            
            # Check data types
            self.assertIsInstance(item["quarter"], str)
            self.assertIsInstance(item["region"], str)
            self.assertIsInstance(item["category"], str)
            self.assertIsInstance(item["sales"], int)

    def test_customer_feedback_structure(self):
        """Test the structure of the customer_feedback dataset."""
        customer_feedback = SAMPLE_DATASETS["customer_feedback"]
        
        # Check the name and description
        self.assertEqual(customer_feedback["name"], "Customer Feedback Survey")
        self.assertIn("customer satisfaction", customer_feedback["description"])
        
        # Check the sample data structure
        sample = customer_feedback["sample"]
        for item in sample:
            self.assertIn("customer_id", item)
            self.assertIn("rating", item)
            self.assertIn("comment", item)
            
            # Check data types
            self.assertIsInstance(item["customer_id"], int)
            self.assertIsInstance(item["rating"], float)
            self.assertIsInstance(item["comment"], str)
            
            # Check rating range
            self.assertGreaterEqual(item["rating"], 0)
            self.assertLessEqual(item["rating"], 5)


if __name__ == "__main__":
    unittest.main() 