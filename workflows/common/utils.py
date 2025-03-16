"""
Utility functions for the CrewAI flow.
"""

import os
import sys
import ray
from typing import Optional, Tuple, Any

# Ray configuration from environment variables with defaults
RAY_TASK_NUM_CPUS = float(os.environ.get("RAY_TASK_NUM_CPUS", "0.1"))
RAY_TASK_MAX_RETRIES = int(os.environ.get("RAY_TASK_MAX_RETRIES", "3"))
RAY_TASK_TIMEOUT = float(os.environ.get("RAY_TASK_TIMEOUT", "10.0"))
RAY_BATCH_SIZE = int(os.environ.get("RAY_BATCH_SIZE", "1"))
RAY_INIT_NUM_CPUS = int(os.environ.get("RAY_INIT_NUM_CPUS", "2"))
RAY_DASHBOARD_PORT = os.environ.get("RAY_DASHBOARD_PORT", "None")  # Use "None" for no dashboard

def apply_ray_patch():
    """Apply patch for Ray's FilteredStream isatty error."""
    try:
        class PatchedStream:
            def __init__(self, stream):
                self.stream = stream
            
            def __getattr__(self, attr):
                if attr == 'isatty':
                    return lambda: False
                return getattr(self.stream, attr)
            
            def write(self, *args, **kwargs):
                return self.stream.write(*args, **kwargs)
            
            def flush(self):
                return self.stream.flush()
        
        # Apply the patch to stdout and stderr
        sys.stdout = PatchedStream(sys.stdout)
        sys.stderr = PatchedStream(sys.stderr)
        print("Applied patch for Ray's FilteredStream isatty error")
        return True
    except Exception as e:
        print(f"Failed to apply Ray patch: {e}")
        return False

def initialize_ray(is_kodosumi: bool = False) -> bool:
    """
    Initialize Ray if not already initialized and not in Kodosumi environment.
    
    Args:
        is_kodosumi: Whether we're running in Kodosumi environment
        
    Returns:
        bool: Whether Ray was successfully initialized
    """
    if ray.is_initialized() or is_kodosumi:
        return True
    
    # Apply patch for Ray's FilteredStream isatty error
    apply_ray_patch()
    
    print("Initializing local Ray instance")
    try:
        # Try to connect to an existing Ray cluster first
        try:
            ray.init(address="auto", ignore_reinit_error=True)
            print("Connected to existing Ray cluster")
        except (ConnectionError, ValueError):
            # If connecting fails, start a new Ray instance with configured resources
            dashboard_port = None if RAY_DASHBOARD_PORT == "None" else int(RAY_DASHBOARD_PORT)
            ray.init(num_cpus=RAY_INIT_NUM_CPUS, dashboard_port=dashboard_port, ignore_reinit_error=True)
            print(f"Started new Ray instance with {RAY_INIT_NUM_CPUS} CPUs")
        return True
    except Exception as ray_init_error:
        print(f"Error initializing Ray: {ray_init_error}")
        print("Continuing without Ray parallelization")
        return False

def test_ray_connectivity() -> Tuple[bool, Any]:
    """
    Test if Ray is working properly by running a simple remote task.
    
    This function tests Ray connectivity by executing a simple remote function
    and checking if it completes successfully within the timeout period.
    
    Returns:
        Tuple[bool, Any]: A tuple containing:
            - A boolean indicating whether the test was successful
            - The result of the test task if successful, or None if failed
    """
    if not ray.is_initialized():
        print("Ray is not initialized. Cannot test connectivity.")
        return False, None
    
    try:
        # Define a simple remote function for testing
        @ray.remote(num_cpus=RAY_TASK_NUM_CPUS, max_retries=RAY_TASK_MAX_RETRIES)
        def ray_test():
            return "Ray test successful"
        
        # Run the test task with a timeout
        result = ray.get(ray_test.remote(), timeout=RAY_TASK_TIMEOUT)
        print(result)
        return True, result
    except (ray.exceptions.GetTimeoutError, TimeoutError) as e:
        print(f"Ray test failed due to timeout: {e}")
        return False, None
    except Exception as e:
        print(f"Ray test failed with error: {e}")
        return False, None

def shutdown_ray(is_kodosumi: bool = False):
    """
    Shutdown Ray if we initialized it and not in Kodosumi environment.
    
    Args:
        is_kodosumi: Whether we're running in Kodosumi environment
    """
    if ray.is_initialized() and not is_kodosumi:
        print("Shutting down Ray...")
        ray.shutdown()
        print("Ray shutdown complete.") 