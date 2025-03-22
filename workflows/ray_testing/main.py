#!/usr/bin/env python

import json
import os
import ray
import sys
import time
import logging
import uuid
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from pydantic import BaseModel
from kodosumi.dtypes import Markdown
from kodosumi.tracer import markdown

# Import Ray test modules
from workflows.ray_testing.ray_tests import (
    basic_test, 
    parallel_test,
    actor_model_test
)

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Check if we're running in Kodosumi environment
# Kodosumi will handle Ray initialization for us
is_kodosumi = os.environ.get("KODOSUMI_ENVIRONMENT") == "true"

def initialize_ray():
    """Initialize Ray if it's not already initialized and we're not in Kodosumi"""
    if not ray.is_initialized() and not is_kodosumi:
        logger.info("Initializing Ray...")
        ray.init(ignore_reinit_error=True)
        logger.info(f"Ray initialized. Dashboard URL: {ray.get_dashboard_url()}")

def shutdown_ray():
    """Shutdown Ray if we initialized it (not in Kodosumi environment)"""
    if ray.is_initialized() and not is_kodosumi:
        logger.info("Shutting down Ray...")
        ray.shutdown()
        logger.info("Ray shutdown complete")

def run_test(test_name: str) -> str:
    """
    Run the specified Ray test
    
    Args:
        test_name: The name of the test to run
        
    Returns:
        Markdown-formatted result string
    """
    logger.info(f"Running Ray test: {test_name}")
    markdown(f"**Starting Ray test: {test_name}**")
    
    test_functions = {
        "basic": basic_test,
        "parallel": parallel_test,
        "actor": actor_model_test
    }
    
    if test_name not in test_functions:
        error_message = f"Error: Test '{test_name}' not found. Available tests: {', '.join(test_functions.keys())}"
        logger.error(error_message)
        markdown(f"**{error_message}**")
        return f"# Ray Test Error\n\n{error_message}"
    
    try:
        # Run the selected test
        start_time = time.time()
        result = test_functions[test_name]()
        elapsed_time = time.time() - start_time
        
        # Log and return results
        logger.info(f"Test '{test_name}' completed in {elapsed_time:.2f} seconds")
        markdown(f"**Test '{test_name}' completed in {elapsed_time:.2f} seconds**")
        
        return result
    except Exception as e:
        error_message = f"Error executing test '{test_name}': {str(e)}"
        logger.error(error_message, exc_info=True)
        markdown(f"**{error_message}**")
        return f"# Ray Test Error\n\n{error_message}\n\n```\n{str(e)}\n```"

def kickoff(inputs: dict = None):
    """
    Kickoff function for the workflow.
    This is the entry point for the workflow when called from Kodosumi.
    """
    # Initialize Ray if needed
    initialize_ray()
    
    try:
        # Extract test name from inputs
        test_name = inputs.get("test_name", "basic") if inputs else "basic"
        logger.info(f"Starting Ray test workflow with test: {test_name}")
        
        # Begin workflow
        markdown(f"**Beginning Ray test workflow: {test_name}**")
        
        # Run the test
        result = run_test(test_name)
        
        logger.info("Ray test workflow completed successfully")
        return Markdown(body=result)
    except Exception as e:
        logger.error(f"Error during Ray test execution: {e}", exc_info=True)
        error_message = f"# Ray Test Error\n\nAn error occurred during test execution:\n\n```\n{str(e)}\n```"
        return Markdown(body=error_message)
    finally:
        # Shutdown Ray if needed
        shutdown_ray()

# Add metadata to the kickoff function
kickoff.__brief__ = {
    "summary": "Ray Feature Testing",
    "description": "Run different Ray tests to explore and debug Ray features in Kodosumi",
    "author": "Kodosumi AI Team",
    "organization": "Kodosumi"
}

if __name__ == "__main__":
    """Main entry point for the workflow when run directly."""
    try:
        # Parse command line arguments
        args = {}
        for arg in sys.argv[1:]:
            if "=" in arg:
                key, value = arg.split("=", 1)
                args[key] = value
        
        logger.info(f"Starting workflow with command line arguments: {args}")
        
        # Run the workflow
        result = kickoff(args)
        
        # Print the result (extract body from Markdown object if needed)
        if hasattr(result, 'body'):
            print("\n" + result.body)
        else:
            print("\n" + str(result))
    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True)
        print(f"\nError: {e}")
        sys.exit(1) 