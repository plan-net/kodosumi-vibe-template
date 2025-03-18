"""
Tests for the logging utility module.
"""

import logging
import pytest
from unittest.mock import patch, MagicMock

from workflows.common.logging_utils import (
    get_logger, log_errors, format_error_response, logger
)

class TestLoggingUtils:
    """Tests for the logging utilities."""
    
    def test_get_logger(self):
        """Test that get_logger returns a properly configured logger."""
        test_logger = get_logger("test_logger")
        
        assert isinstance(test_logger, logging.Logger)
        assert test_logger.name == "test_logger"
        assert len(test_logger.handlers) > 0
        assert test_logger.level in [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]
    
    def test_global_logger(self):
        """Test that the global logger is properly configured."""
        assert isinstance(logger, logging.Logger)
        assert logger.name == "workflows"
    
    def test_log_errors_decorator_no_error(self):
        """Test that the log_errors decorator passes through when no error occurs."""
        mock_logger = MagicMock()
        
        @log_errors(logger=mock_logger)
        def test_func():
            return "success"
        
        result = test_func()
        
        assert result == "success"
        mock_logger.error.assert_not_called()
    
    def test_log_errors_decorator_with_error(self):
        """Test that the log_errors decorator logs errors properly."""
        mock_logger = MagicMock()
        test_error = ValueError("Test error")
        
        @log_errors(logger=mock_logger, error_msg="Custom error message")
        def test_func():
            raise test_error
        
        result = test_func()
        
        assert result is None  # Default behavior is to return None without reraising
        mock_logger.error.assert_called_once()
        # Check that the error message contains our custom message and the error itself
        assert "Custom error message" in mock_logger.error.call_args[0][0]
        assert "Test error" in mock_logger.error.call_args[0][0]
    
    def test_log_errors_decorator_reraise(self):
        """Test that the log_errors decorator can reraise errors."""
        mock_logger = MagicMock()
        
        @log_errors(logger=mock_logger, reraise=True)
        def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            test_func()
        
        mock_logger.error.assert_called_once()
    
    def test_format_error_response(self):
        """Test that format_error_response creates a properly formatted response."""
        test_error = ValueError("Test error message")
        
        response = format_error_response(test_error)
        
        assert "error" in response
        assert response["error"]["type"] == "ValueError"
        assert response["error"]["message"] == "Test error message"
        assert "timestamp" in response["error"]
    
    def test_format_error_response_with_context(self):
        """Test that format_error_response includes context information."""
        test_error = ValueError("Test error message")
        context = {"dataset": "test_dataset", "step": "analyze_data"}
        
        response = format_error_response(test_error, context)
        
        assert "context" in response["error"]
        assert response["error"]["context"] == context