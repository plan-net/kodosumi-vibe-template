"""
Common data structures and sample datasets for CrewAI workflows.
"""

# Sample datasets for testing and demonstration
SAMPLE_DATASETS = {
    "sales_data": {
        "name": "Quarterly Sales Data",
        "description": "Sales data by quarter, region, and product category.",
        "sample": [
            {"quarter": "Q1", "region": "North", "category": "Electronics", "sales": 150000},
            {"quarter": "Q1", "region": "South", "category": "Furniture", "sales": 120000},
            {"quarter": "Q2", "region": "East", "category": "Electronics", "sales": 180000},
            {"quarter": "Q2", "region": "West", "category": "Furniture", "sales": 140000},
            {"quarter": "Q3", "region": "North", "category": "Clothing", "sales": 90000},
            {"quarter": "Q3", "region": "South", "category": "Electronics", "sales": 200000},
            {"quarter": "Q4", "region": "East", "category": "Furniture", "sales": 160000},
            {"quarter": "Q4", "region": "West", "category": "Clothing", "sales": 110000}
        ]
    },
    "customer_feedback": {
        "name": "Customer Feedback Survey",
        "description": "Results from a recent customer satisfaction survey with ratings and comments.",
        "sample": [
            {"customer_id": 1001, "rating": 4.5, "comment": "Great product, fast delivery!"},
            {"customer_id": 1002, "rating": 3.0, "comment": "Product was okay, but shipping took too long."},
            {"customer_id": 1003, "rating": 5.0, "comment": "Excellent customer service and quality."},
            {"customer_id": 1004, "rating": 2.5, "comment": "The product didn't meet my expectations."},
            {"customer_id": 1005, "rating": 4.0, "comment": "Good value for money, would recommend."}
        ]
    }
} 