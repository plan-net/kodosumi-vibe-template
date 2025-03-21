"""
Integration tests for the Hypothesis Generator workflow.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from workflows.hypothesis_generator.main import HypothesisGeneratorFlow, kickoff
from workflows.hypothesis_generator.crews.hypothesis_crew.hypothesis_crew import HypothesisCrew


@pytest.mark.asyncio
async def test_kickoff_function():
    """Test that the kickoff function initializes and runs the flow."""
    # Test inputs
    test_inputs = {
        "brand": "Test Brand",
        "product": "Test Product",
        "audience": "Test Audience",
        "goal": "Test Goal",
        "output_format": "markdown"
    }
    
    # Mock ray initialization
    with patch('workflows.hypothesis_generator.main.initialize_ray') as mock_init_ray, \
         patch('workflows.hypothesis_generator.main.shutdown_ray') as mock_shutdown_ray, \
         patch.object(HypothesisGeneratorFlow, 'kickoff_async') as mock_kickoff:
        
        # Mock flow.kickoff_async to return a test result
        mock_kickoff.return_value = "Test result"
        
        # Call the kickoff function
        result = await kickoff(test_inputs)
        
        # Check ray was initialized and shutdown
        mock_init_ray.assert_called_once()
        mock_shutdown_ray.assert_called_once()
        
        # Check the flow was run with correct inputs
        mock_kickoff.assert_called_once()
        
        # Check the result is returned
        assert result == "Test result"


@pytest.mark.asyncio
async def test_flow_with_real_crews_mocked():
    """
    Test the flow with real crew objects but mocked execution.
    This tests the integration between flow and crew but doesn't actually run the LLM.
    """
    # Mock the HypothesisCrew entirely at the module level
    mock_crew_instance = MagicMock()
    mock_crew = MagicMock()
    mock_crew_instance.crew.return_value = mock_crew
    
    # Mock the crew kickoff to return structured data
    mock_result = MagicMock()
    mock_crew.kickoff.return_value = mock_result
    
    # Mock the data for extract_structured_data
    mock_data = {
        "research": {"summary": "Research summary", "sources": []},
        "obvious_hypotheses": [{"hypothesis": "Obvious hypothesis"}],
        "innovative_hypotheses": [{"hypothesis": "Innovative hypothesis"}]
    }
    
    # Use patch to replace the HypothesisCrew constructor
    with patch('workflows.hypothesis_generator.main.HypothesisCrew', return_value=mock_crew_instance), \
         patch('workflows.hypothesis_generator.main.extract_structured_data', return_value=mock_data), \
         patch('workflows.hypothesis_generator.main.format_output', return_value="Formatted output"):
        
        # Create the flow with test inputs
        state = {
            "brand": "Integration Test Brand",
            "product": "Integration Test Product",
            "audience": "Integration Test Audience",
            "goal": "Integration Test Goal",
            "output_format": "markdown"
        }
        
        flow = HypothesisGeneratorFlow()
        for key, value in state.items():
            setattr(flow.state, key, value)
        
        # Execute the flow
        result = await flow.kickoff_async()
        
        # Check the crew was used correctly
        mock_crew_instance.crew.assert_called_once()
        mock_crew.kickoff.assert_called_once()
        
        # Check the flow processed the data correctly
        assert flow.state.research_results == mock_data["research"]
        assert flow.state.obvious_hypotheses == mock_data["obvious_hypotheses"]
        assert flow.state.innovative_hypotheses == mock_data["innovative_hypotheses"]
        
        # Check the final result
        assert result == "Formatted output"