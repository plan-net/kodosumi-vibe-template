"""
Ray Parallel Processing Demo

This script demonstrates how to use Ray for parallel processing of multiple tasks:
1. Initializing a Ray cluster
2. Defining a remote function for data processing
3. Submitting multiple tasks to be executed in parallel
4. Gathering and aggregating results
5. Organizing results by priority

This pattern is used in Kodosumi's workflow's `process_insights_in_parallel` method
and other places where parallel processing is needed.
"""
import ray
import time
import random
import uuid
from datetime import datetime

print("Step 1: Initializing Ray cluster...")
# Initialize Ray
ray.init()
print(f"Ray initialized! Available resources: {ray.available_resources()}")

# Define a remote function similar to process_insight
@ray.remote
def process_insight(insight):
    """
    Ray remote function to process a single insight.
    
    This simulates real-world processing like:
    - Natural language processing
    - Priority scoring
    - Metadata enrichment
    
    In a real application, this might call a machine learning model
    or perform complex data transformations.
    
    Args:
        insight: The insight text to process
        
    Returns:
        A dictionary with the processed insight data
    """
    # Get information about the worker executing this task
    worker_id = ray.get_runtime_context().get_node_id()
    worker_ip = ray.get_runtime_context().get_node_ip_address()
    
    # Simulate varying processing times to show asynchronous nature
    processing_time = random.uniform(0.5, 1.5)
    time.sleep(processing_time)
    
    # Generate a priority score (in a real app, this would use ML/rules)
    priority = random.randint(1, 10)
    
    # Compile the result with metadata
    result = {
        "insight": insight,
        "priority": priority,
        "processed_by": f"Ray-Worker-{uuid.uuid4().hex[:8]}",
        "worker_id": worker_id,
        "worker_ip": worker_ip,
        "processing_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "processing_duration": f"{processing_time:.2f}s",
    }
    
    return result

def main():
    """Main function to demonstrate Ray parallel processing."""
    # Sample insights - in a real app, these would come from a database or API
    insights = [
        "Sales have increased by 15% in Q2",
        "Customer retention rate has improved by 8%",
        "Mobile users account for 60% of traffic",
        "Average order value has decreased by 5%",
        "New user registration is up 20% month-over-month"
    ]
    
    print(f"\nStep 2: Processing {len(insights)} insights in parallel...")
    start_time = time.time()
    
    # This is the key pattern for parallel processing:
    # 1. Create a list of remote function references (doesn't execute yet)
    # 2. Use ray.get() to retrieve all results when ready
    print("  Submitting tasks to Ray workers...")
    refs = [process_insight.remote(insight) for insight in insights]
    
    # This blocks until all tasks are complete
    print("  Waiting for all tasks to complete...")
    insights_results = ray.get(refs)
    
    processing_time = time.time() - start_time
    
    print(f"\nStep 3: Processing completed in {processing_time:.2f} seconds")
    print(f"  Note: Sequential processing would take at least {sum([float(r['processing_duration'][:-1]) for r in insights_results]):.2f} seconds")
    
    # Group insights by priority - a common pattern in real applications
    print("\nStep 4: Organizing results by priority...")
    high_priority = [i for i in insights_results if i.get('priority', 0) >= 8]
    medium_priority = [i for i in insights_results if 4 <= i.get('priority', 0) < 8]
    low_priority = [i for i in insights_results if i.get('priority', 0) < 4]
    
    # Print summary
    print(f"  Total processed: {len(insights_results)}")
    print(f"  High priority: {len(high_priority)}")
    print(f"  Medium priority: {len(medium_priority)}")
    print(f"  Low priority: {len(low_priority)}")
    
    # Show the processed insights
    print("\nStep 5: Detailed Results:")
    for i, result in enumerate(insights_results, 1):
        priority_label = "HIGH" if result['priority'] >= 8 else "MEDIUM" if result['priority'] >= 4 else "LOW"
        print(f"{i}. '{result['insight']}' (Priority: {result['priority']} - {priority_label})")
        print(f"   Processed by: {result['processed_by']}")
        print(f"   Worker ID: {result['worker_id']}")
        print(f"   Processing time: {result['processing_time']} (duration: {result['processing_duration']})")
        print()
    
    # Shutdown Ray
    print("Step 6: Shutting down Ray...")
    ray.shutdown()
    print("Ray shutdown complete.")
    print("\nThis demonstrates how Ray enables efficient parallel processing in Kodosumi workflows.")

if __name__ == "__main__":
    main() 