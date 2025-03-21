"""
Basic tests for the Hypothesis Generator workflow.
"""

import pytest
from unittest.mock import patch, MagicMock
import json

from workflows.hypothesis_generator.main import HypothesisGeneratorFlow, HypothesisGeneratorState


class TestHypothesisGeneratorFlow:
    """Tests for the HypothesisGeneratorFlow class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a state with all required fields
        state = HypothesisGeneratorState()
        state.brand = "Test Brand"
        state.product = "Test Product"
        state.audience = "Test Audience"
        state.goal = "Test Goal"
        state.output_format = "markdown"
        
        self.state = state
        self.flow = HypothesisGeneratorFlow(self.state)
    
    def test_state_initialization(self):
        """Test that the state is initialized correctly."""
        assert self.state.brand == "Test Brand"
        assert self.state.product == "Test Product"
        assert self.state.audience == "Test Audience"
        assert self.state.goal == "Test Goal"
        assert self.state.output_format == "markdown"
        assert isinstance(self.state.research_results, dict)
        assert isinstance(self.state.obvious_hypotheses, list)
        assert isinstance(self.state.innovative_hypotheses, list)
        assert isinstance(self.state.final_results, dict)
    
    def test_validate_inputs_with_valid_inputs(self):
        """Test validation with valid inputs."""
        result = self.flow.validate_inputs()
        # When validation succeeds, result should be None (no error handler called)
        assert result is None
    
    def test_validate_inputs_with_missing_inputs(self):
        """Test validation with missing inputs."""
        # Create a state with missing brand
        state = HypothesisGeneratorState()
        # Directly modify the state to ensure empty brand
        state.brand = ""
        state.product = "Test Product"
        state.audience = "Test Audience" 
        state.goal = "Test Goal"
        flow = HypothesisGeneratorFlow(state)
        
        # Mock the handle_flow_error function
        with patch('workflows.hypothesis_generator.main.handle_flow_error') as mock_handle_error:
            mock_handle_error.return_value = "Error response"
            result = flow.validate_inputs()
            
            # Should call the error handler
            mock_handle_error.assert_called_once()
            
            # Check that brand is in the error keyword arguments
            error_arg = mock_handle_error.call_args.kwargs.get('error', '')
            assert 'brand' in error_arg
            assert result == "Error response"
    
    @patch('workflows.hypothesis_generator.main.HypothesisCrew')
    def test_generate_hypotheses(self, mock_crew_class):
        """Test the generate_hypotheses method with mocked crew."""
        # Ensure the state has the correct values
        self.flow.state.brand = "Test Brand" 
        self.flow.state.product = "Test Product"
        self.flow.state.audience = "Test Audience"
        self.flow.state.goal = "Test Goal"
        
        # Mock the crew and its kickoff method
        mock_crew_instance = MagicMock()
        mock_crew = MagicMock()
        mock_crew_instance.crew.return_value = mock_crew
        mock_crew_class.return_value = mock_crew_instance
        
        # Mock crew result with structured data
        mock_crew_result = MagicMock()
        mock_crew.kickoff.return_value = mock_crew_result
        
        # Mock extract_structured_data
        mock_json_data = {
            "research": {"summary": "Test summary", "sources": []},
            "obvious_hypotheses": [{"hypothesis": "Test obvious hypothesis"}],
            "innovative_hypotheses": [{"hypothesis": "Test innovative hypothesis"}]
        }
        
        with patch('workflows.hypothesis_generator.main.extract_structured_data') as mock_extract:
            mock_extract.return_value = mock_json_data
            
            # Run the method
            result = self.flow.generate_hypotheses()
            
            # Check that the crew was created and kicked off with the right inputs
            mock_crew_class.assert_called_once()
            mock_crew_instance.crew.assert_called_once()
            mock_crew.kickoff.assert_called_once()
            
            # Get the inputs passed to kickoff
            kickoff_inputs = mock_crew.kickoff.call_args.kwargs['inputs']
            assert kickoff_inputs['brand'] == "Test Brand"
            assert kickoff_inputs['product'] == "Test Product"
            
            # Check that the state was updated
            assert self.flow.state.research_results == mock_json_data["research"]
            assert self.flow.state.obvious_hypotheses == mock_json_data["obvious_hypotheses"]
            assert self.flow.state.innovative_hypotheses == mock_json_data["innovative_hypotheses"]
            
            # Check that it returns the expected next step
            assert result == self.flow.finalize_results
    
    def test_finalize_results(self):
        """Test the finalize_results method."""
        # Set up the state with the required values
        self.flow.state.brand = "Test Brand"
        self.flow.state.product = "Test Product"
        self.flow.state.audience = "Test Audience"
        self.flow.state.goal = "Test Goal"
        
        # Set up test data in the state
        self.flow.state.research_results = {"summary": "Test summary", "sources": [{"url": "http://example.com"}]}
        self.flow.state.obvious_hypotheses = [{"hypothesis": "Test obvious hypothesis"}]
        self.flow.state.innovative_hypotheses = [{"hypothesis": "Test innovative hypothesis"}]
        
        # Mock format_output
        with patch('workflows.hypothesis_generator.main.format_output') as mock_format:
            mock_format.return_value = "Formatted output"
            
            # Run the method
            result = self.flow.finalize_results()
            
            # Check that format_output was called with the right arguments
            mock_format.assert_called_once()
            final_results = mock_format.call_args.args[0]
            
            # Check the structure of the final results
            assert final_results["brand"] == "Test Brand"
            assert final_results["product"] == "Test Product"
            assert final_results["research_summary"] == "Test summary"
            assert len(final_results["sources"]) == 1
            assert final_results["obvious_hypotheses"] == [{"hypothesis": "Test obvious hypothesis"}]
            assert final_results["innovative_hypotheses"] == [{"hypothesis": "Test innovative hypothesis"}]
            
            # Check the return value
            assert result == "Formatted output"