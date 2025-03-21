"""
Basic Ray Demo Script

This script demonstrates the fundamental concepts of using Ray for distributed computing:
1. Initializing Ray
2. Defining a remote function
3. Submitting tasks to Ray workers
4. Retrieving results

This pattern is used throughout the Kodosumi codebase for distributed processing.
"""
import ray
import time

# Initialize Ray
# This connects to an existing Ray cluster or starts a new one locally
print("Step 1: Initializing Ray...")
ray.init()
print(f"Ray initialized! Resources available: {ray.available_resources()}")

# Define a remote function
# The @ray.remote decorator marks this function to run on a Ray worker
@ray.remote
def hello_world():
    """
    This is a simple Ray remote function that:
    1. Simulates work with a sleep
    2. Returns a result
    
    When called with .remote(), this doesn't execute immediately, but returns a reference
    """
    worker_id = ray.get_runtime_context().get_node_id()
    time.sleep(1)  # Simulate some processing time
    return f"Hello, Ray! Processed by worker {worker_id}"

# Call the remote function
# This submits the task to Ray's scheduler, which will assign it to an available worker
print("\nStep 2: Submitting task to Ray...")
ref = hello_world.remote()
print(f"Task submitted! Reference ID: {ref}")
print("Notice that we got a reference immediately without waiting for the result")

# Get the result
# This blocks until the task completes and returns the actual result
print("\nStep 3: Waiting for result...")
result = ray.get(ref)
print(f"Result received: {result}")

# Demonstrate parallel execution
print("\nStep 4: Submitting multiple tasks in parallel...")
refs = [hello_world.remote() for _ in range(5)]
print(f"Submitted 5 tasks with references: {refs}")

# Get all results
print("\nStep 5: Waiting for all results...")
results = ray.get(refs)
for i, result in enumerate(results):
    print(f"Result {i+1}: {result}")

# Shutdown Ray
# This isn't always necessary, but it's good practice for demos and tests
print("\nStep 6: Shutting down Ray...")
ray.shutdown()
print("Ray shutdown complete.") 