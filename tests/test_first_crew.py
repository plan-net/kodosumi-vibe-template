import os
import json
import pytest
from unittest.mock import patch, MagicMock

from workflows.crewai_flow.crews.first_crew.first_crew import FirstCrew, DataAnalysisOutput, BusinessInsightsOutput

# Sample data for testing
SAMPLE_DATA = {
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

# Sample task outputs for mocking
SAMPLE_DATA_ANALYSIS_OUTPUT = DataAnalysisOutput(
    patterns=["High ratings correlate with positive delivery experiences", 
              "Lower ratings mention unmet expectations"],
    trends=["Average rating is approximately 3.8 out of 5", 
            "Delivery time is a common concern"],
    analysis="The customer feedback shows generally positive sentiment with specific concerns around delivery times and product expectations."
)

SAMPLE_BUSINESS_INSIGHTS_OUTPUT = BusinessInsightsOutput(
    summary="Customer feedback analysis reveals overall positive satisfaction with specific improvement areas.",
    insights=["High ratings correlate with mentions of customer service and product quality",
              "Shipping and delivery time is a recurring concern across all rating levels",
              "Customers who mention 'value for money' tend to be satisfied overall"],
    recommendations=["Enhance the shipping process to address the most common concern",
                     "Improve product descriptions to better set customer expectations",
                     "Create a loyalty program for highly satisfied customers"]
)

class TestFirstCrew:
    """
    Unit tests for the FirstCrew class.
    """
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Set up environment variables for testing."""
        monkeypatch.setenv("OPENAI_API_KEY", "test_api_key")
    
    @pytest.fixture
    def crew_instance(self, mock_env):
        """Create a FirstCrew instance for testing."""
        return FirstCrew()
    
    def test_initialization(self, crew_instance):
        """Test that the FirstCrew instance initializes correctly."""
        assert crew_instance is not None
        assert hasattr(crew_instance, 'llm')
    
    def test_agent_creation(self, crew_instance):
        """Test that agents are created correctly."""
        data_analyst = crew_instance.data_analyst()
        insights_specialist = crew_instance.insights_specialist()
        
        assert data_analyst is not None
        assert insights_specialist is not None
        assert data_analyst.role != insights_specialist.role
    
    def test_task_creation(self, crew_instance):
        """Test that tasks are created correctly."""
        analyze_task = crew_instance.analyze_data_task()
        insights_task = crew_instance.generate_insights_task()
        
        assert analyze_task is not None
        assert insights_task is not None
        assert analyze_task.output_pydantic == DataAnalysisOutput
        assert insights_task.output_pydantic == BusinessInsightsOutput
    
    def test_crew_creation(self, crew_instance):
        """Test that the crew is created correctly."""
        crew = crew_instance.crew()
        
        assert crew is not None
        assert len(crew.agents) == 2
        assert len(crew.tasks) == 2
    
    @patch('crewai.Crew.kickoff')
    def test_crew_execution(self, mock_kickoff, crew_instance):
        """Test that the crew executes correctly with mocked responses."""
        # Create a mock crew result
        mock_result = MagicMock()
        mock_result.tasks_output = [SAMPLE_DATA_ANALYSIS_OUTPUT, SAMPLE_BUSINESS_INSIGHTS_OUTPUT]
        mock_kickoff.return_value = mock_result
        
        # Get the crew
        crew = crew_instance.crew()
        
        # Prepare task inputs
        task_inputs = {
            "dataset_name": SAMPLE_DATA["name"],
            "dataset_description": SAMPLE_DATA["description"],
            "sample_data": json.dumps(SAMPLE_DATA["sample"], indent=2)
        }
        
        # Run the crew
        crew_result = crew.kickoff(inputs=task_inputs)
        
        # Check that kickoff was called with the correct inputs
        mock_kickoff.assert_called_once_with(inputs=task_inputs)
        
        # Check the result
        assert hasattr(crew_result, 'tasks_output')
        assert len(crew_result.tasks_output) == 2
        
        # Check the first task output (data analysis)
        data_analysis = crew_result.tasks_output[0]
        assert isinstance(data_analysis, DataAnalysisOutput)
        assert len(data_analysis.patterns) == 2
        assert len(data_analysis.trends) == 2
        assert data_analysis.analysis is not None
        
        # Check the second task output (business insights)
        business_insights = crew_result.tasks_output[1]
        assert isinstance(business_insights, BusinessInsightsOutput)
        assert business_insights.summary is not None
        assert len(business_insights.insights) == 3
        assert len(business_insights.recommendations) == 3 