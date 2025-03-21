# Ray Demo Scripts

This directory contains example scripts that demonstrate how to use Ray for distributed computing within the Kodosumi framework.

## Available Examples

1. **ray_test.py**: A simple Ray example demonstrating how to:
   - Initialize Ray
   - Define a remote function
   - Submit tasks to Ray workers
   - Retrieve results

2. **ray_parallel_test.py**: A more advanced Ray example demonstrating:
   - Parallel processing of multiple tasks
   - Task result aggregation
   - Worker identification
   - Processing time tracking
   - Priority-based result organization

3. **ray_actor_model.py**: Demonstrates Ray's Actor model for stateful processing:
   - Creating actor instances with specializations
   - Maintaining state across method calls
   - Routing tasks to appropriate actors
   - Tracking processing history and statistics

4. **run_all_examples.py**: A utility script to run all examples sequentially:
   - Can run all examples or specific ones via command line args
   - Handles Ray initialization and cleanup
   - Provides a summary of results

## Running the Examples

To run all examples at once:

```bash
# Run all examples
python examples/ray/run_all_examples.py

# Run only a specific example
python examples/ray/run_all_examples.py basic     # Just the basic example
python examples/ray/run_all_examples.py parallel  # Just the parallel example
python examples/ray/run_all_examples.py actor     # Just the actor example
```

Or run individual examples:

```bash
# Make sure Ray is running
ray status

# If Ray isn't running, start it
ray start --head

# Run the basic example
python examples/ray/ray_test.py

# Run the parallel processing example
python examples/ray/ray_parallel_test.py

# Run the actor model example
python examples/ray/ray_actor_model.py
```

## How These Relate to Kodosumi

The Kodosumi framework uses Ray for distributed computing in several ways:

1. Running CrewAI flows in parallel
2. Processing insights in parallel using remote functions
3. Distributing workloads across available compute resources
4. Maintaining state in long-running agents and workflows

These examples demonstrate the core Ray patterns that are used throughout the codebase:

- **Basic remote execution** (ray_test.py): Used for simple task offloading
- **Parallel processing** (ray_parallel_test.py): Used in the `process_insights_in_parallel` method
- **Actor model** (ray_actor_model.py): Useful for stateful agents and workflow components

## Ray Dashboard

You can view the Ray dashboard to monitor task execution, resource utilization, and cluster status:

```
http://127.0.0.1:8265
```

## Additional Resources

To learn more about Ray and how it's used in the Kodosumi framework:

- [Ray documentation](https://docs.ray.io/)
- [Ray Tutorials](https://docs.ray.io/en/latest/ray-overview/getting-started.html)
- Look at the `workflows/example/main.py` file to see how Ray is used in CrewAI flows 