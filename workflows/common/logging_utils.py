"""
Centralized logging utilities for the CrewAI workflows.
Provides consistent logging configuration and error handling throughout the application.
"""

import logging
import os
import sys
import traceback
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, TypeVar, cast

# Type variable for decorators
F = TypeVar('F', bound=Callable[..., Any])

# Configure logging levels from environment with fallback to INFO
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.environ.get(
    "LOG_FORMAT", 
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Dictionary to map string log levels to logging constants
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance with consistent formatting.
    
    Args:
        name: The logger name, typically __name__ from the calling module
        
    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if it's not already configured to avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(LOG_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Set the log level from environment or default
        logger.setLevel(LOG_LEVELS.get(LOG_LEVEL, logging.INFO))
    
    return logger

def log_errors(
    logger: Optional[logging.Logger] = None,
    exception_types: tuple = (Exception,),
    error_msg: str = "An error occurred",
    reraise: bool = False
) -> Callable[[F], F]:
    """
    Decorator that catches and logs exceptions.
    
    Args:
        logger: Logger instance to use. If None, a new logger will be created
        exception_types: Tuple of exception types to catch
        error_msg: Message to log when an exception occurs
        reraise: Whether to re-raise the exception after logging
        
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get logger if not provided
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)
            
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                trace = traceback.format_exc()
                logger.error(f"{error_msg}: {str(e)}\n{trace}")
                
                if reraise:
                    raise
                
                # Return None or other default value when not reraising
                return None
                
        return cast(F, wrapper)
    return decorator

def format_error_response(
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format an error response with consistent structure.
    
    Args:
        error: The exception that occurred
        context: Additional context information
        
    Returns:
        A dictionary with error information
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    response = {
        "error": {
            "type": error_type,
            "message": error_message,
            "timestamp": logging.Formatter.formatTime(logging.Formatter(), logging.LogRecord(
                "", logging.ERROR, "", 0, "", (), None, None
            ))
        }
    }
    
    # Add context if provided
    if context:
        response["error"]["context"] = context
    
    return response

# Global logger instance for direct import
logger = get_logger("workflows")